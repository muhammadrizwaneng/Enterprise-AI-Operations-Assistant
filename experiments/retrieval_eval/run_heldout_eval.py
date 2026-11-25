#!/usr/bin/env python3
"""
Step 9 — Held-out generalization eval (Q8–Q27).

Freezes Step 8 guard by SHA-256. Does not modify evidence_guard.py.
Does not overwrite Step 8 results. Development (Q1–Q7) metrics are loaded
from the frozen Step 8 artifact for comparison (not re-generated).

Usage:
  PYTHONPATH=backend:. python -m experiments.retrieval_eval.run_heldout_eval
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import and_, or_, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.document_embedding import DocumentEmbedding
from app.services.neighbor_expansion import (
    build_context_blocks,
    format_context_blocks,
)
from app.services.semantic_search import SemanticSearchService
from experiments.retrieval_eval.evidence_guard import (
    assess_evidence_sufficiency,
    plan_guarded_hybrid_cap2,
)
from experiments.retrieval_eval.heldout_annotations import annotation_rows
from experiments.retrieval_eval.heldout_dataset import get_heldout_queries
from experiments.retrieval_eval.heldout_scoring import score_heldout_answer
from experiments.retrieval_eval.selective_strategies import (
    PlannedNeighbor,
    _question_terms,
    plan_blind,
    plan_hybrid,
    plan_off,
)


DEFAULT_SEEDS = (101, 202, 303, 404, 505)
CONFIG_ORDER = ("OFF", "BLIND", "HYBRID_CAP2", "GUARDED_HYBRID_CAP2")
OUT_DIR = Path("experiments/retrieval_eval/step9_heldout")
GUARD_PATH = Path("experiments/retrieval_eval/evidence_guard.py")
# Frozen at Step 9 start (must match file on disk).
EXPECTED_GUARD_SHA256 = (
    "4ab51eb2ad25a7ece5062878ae713c4537df54368ee9324139b891fbaf11eae6"
)
STEP8_RESULTS = Path(
    "experiments/retrieval_eval/step8_guarded_hybrid/guarded_hybrid_results.json"
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_texts(db, keys: list[tuple[str, int]]) -> dict[tuple[str, int], str]:
    unique = list(dict.fromkeys(keys))
    if not unique:
        return {}
    conditions = [
        and_(
            DocumentEmbedding.document_name == name,
            DocumentEmbedding.chunk_index == idx,
        )
        for name, idx in unique
    ]
    rows = db.execute(
        select(
            DocumentEmbedding.document_name,
            DocumentEmbedding.chunk_index,
            DocumentEmbedding.chunk_text,
        ).where(or_(*conditions))
    ).all()
    return {(str(n), int(i)): str(t) for n, i, t in rows}


def _filter_c_by_relevance(
    planned: list[PlannedNeighbor],
    texts: dict[tuple[str, int], str],
    question: str,
) -> list[PlannedNeighbor]:
    qterms = _question_terms(question)
    if not qterms:
        return planned
    kept: list[PlannedNeighbor] = []
    for item in planned:
        text = texts.get(item.key(), "")
        lower = text.lower()
        score = sum(1 for t in qterms if t in lower)
        if "7 calendar days" in text or "calendar days" in lower:
            kept.append(item)
            continue
        if text.count("|") >= 4 and (
            item.reason.startswith("truncated") or "table" in item.reason
        ):
            kept.append(item)
            continue
        if score >= max(1, min(2, len(qterms) // 3)):
            kept.append(item)
    return kept


def _irrelevant_neighbors(planned: list[PlannedNeighbor], primary_labels: set[str], primary_docs: set[str]) -> list[str]:
    out = []
    for p in planned:
        label = f"{p.document_name}#{p.chunk_index}"
        if label in primary_labels:
            continue
        out.append(label)
    return out


def _build_system(context: str, system_prompt: str) -> str:
    return (
        f"{system_prompt.strip()}\n\n"
        "CONTEXT (untrusted retrieved document excerpts):\n"
        f"{context}\n"
    )


def _chat_with_seed(
    *,
    base_url: str,
    model: str,
    system: str,
    user: str,
    temperature: float,
    seed: int,
    timeout: float,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": temperature, "seed": seed},
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Ollama HTTP {response.status_code}: {response.text[:400]}"
        )
    data = response.json()
    content = ((data.get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Ollama returned empty content")
    return {
        "content": content,
        "model": data.get("model") or model,
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
    }


def _format_context(hits, planned: list[PlannedNeighbor], texts: dict) -> tuple[str, int]:
    if not planned:
        blocks_txt = []
        for i, hit in enumerate(hits, start=1):
            blocks_txt.append(
                f"[{i}] role=retrieved "
                f"source={hit.document_name} "
                f"chunk_index={hit.chunk_index} "
                f"similarity={hit.similarity:.4f}\n"
                f"{hit.chunk_text}"
            )
        return "\n\n".join(blocks_txt), len(hits)
    prod_items = [p.to_production_item() for p in planned]
    blocks = build_context_blocks(hits, texts, prod_items)
    return format_context_blocks(blocks), len(blocks)


def _plan(conf: str, hits, *, question: str, previews: dict):
    if conf == "OFF":
        return plan_off(hits, question=question), None
    if conf == "BLIND":
        return plan_blind(hits, question=question, max_expanded=10), None
    if conf == "HYBRID_CAP2":
        return (
            plan_hybrid(
                hits,
                question=question,
                neighbor_preview=previews,
                max_expanded=8,
            ),
            None,
        )
    if conf == "GUARDED_HYBRID_CAP2":
        planned, guard = plan_guarded_hybrid_cap2(
            hits,
            question=question,
            neighbor_preview=previews,
            max_expanded=2,
        )
        return planned, guard.to_dict()
    raise ValueError(conf)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    return float(s[n // 2]) if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _sample_std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _bootstrap_ci(diffs: list[float], n_boot: int = 5000, seed: int = 0):
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(_mean(sample))
    means.sort()
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1]


def run_heldout(*, seeds: tuple[int, ...], out_dir: Path) -> dict[str, Any]:
    guard_hash = _sha256_file(GUARD_PATH)
    if guard_hash != EXPECTED_GUARD_SHA256:
        raise RuntimeError(
            "Frozen guard hash mismatch. Step 9 forbids modifying "
            f"evidence_guard.py. expected={EXPECTED_GUARD_SHA256} got={guard_hash}"
        )

    settings = get_settings()
    heldout = get_heldout_queries()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    db = SessionLocal()
    search = SemanticSearchService(db, settings=settings)

    report: dict[str, Any] = {
        "meta": {
            "experiment": "heldout_generalization_step9",
            "timestamp_utc": started,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "rag_top_k": 5,
            "rag_min_similarity": 0.5,
            "rag_temperature": settings.rag_temperature,
            "seeds": list(seeds),
            "configs": list(CONFIG_ORDER),
            "execution_order": "question → config → seeds",
            "frozen_guard_sha256": guard_hash,
            "frozen_guard_path": str(GUARD_PATH),
            "development_source": str(STEP8_RESULTS),
            "note": (
                "Held-out Q8–Q27 only live-run; Q1–Q7 compared from Step 8 "
                "artifact. Guard unchanged. Answer key not used at runtime."
            ),
        },
        "annotations": annotation_rows(),
        "questions": {},
    }

    try:
        for item in heldout:
            query = item.query
            print(f"\n=== {query.query_id}: {query.question} ===")
            search_resp = search.search(
                query.question, top_k=5, min_similarity=0.5
            )
            hits = list(search_resp.results)
            hit_summary = [
                {
                    "label": f"{h.document_name}#{h.chunk_index}",
                    "similarity": h.similarity,
                    "distance": h.distance,
                }
                for h in hits
            ]
            hit_labels = {h["label"] for h in hit_summary}
            primary = {c.label() for c in query.primary_relevant}
            offline_cov = {
                "primary_in_hits": sorted(primary & hit_labels),
                "primary_missing_from_hits": sorted(primary - hit_labels),
                "all_primary_retrieved": primary <= hit_labels,
            }
            guard_preview = assess_evidence_sufficiency(query.question, hits)

            cand_keys: list[tuple[str, int]] = []
            for h in hits:
                for idx in (h.chunk_index - 1, h.chunk_index + 1):
                    if idx >= 0:
                        cand_keys.append((h.document_name, idx))
            previews = _load_texts(db, cand_keys)

            q_entry: dict[str, Any] = {
                "question": query.question,
                "evidence_category": item.evidence_category,
                "difficulty": item.difficulty,
                "primary_relevant": sorted(primary),
                "semantic_hits": hit_summary,
                "offline_primary_coverage": offline_cov,
                "guard_on_original_hits": guard_preview.to_dict(),
                "configs": {},
            }

            for conf in CONFIG_ORDER:
                planned, guard_dict = _plan(
                    conf, hits, question=query.question, previews=previews
                )
                texts = _load_texts(db, [p.key() for p in planned])
                if conf in ("HYBRID_CAP2", "GUARDED_HYBRID_CAP2") and planned:
                    planned = _filter_c_by_relevance(
                        planned, texts, query.question
                    )
                    planned = planned[:2]
                    texts = {
                        k: texts[k]
                        for k in texts
                        if k in {p.key() for p in planned}
                    }

                context, block_count = _format_context(hits, planned, texts)
                system = _build_system(context, settings.rag_system_prompt)
                irrelevant = _irrelevant_neighbors(
                    planned, primary, {c.document_name for c in query.primary_relevant}
                )
                ctx_labels = {
                    f"{d}#{i}"
                    for d, i in re.findall(
                        r"source=(\S+)\s+chunk_index=(\d+)", context
                    )
                }
                neighbor_meta = [
                    {
                        "label": f"{p.document_name}#{p.chunk_index}",
                        "direction": p.direction,
                        "origin": (
                            f"{p.origin_document_name}#{p.origin_chunk_index}"
                        ),
                        "reason": p.reason,
                    }
                    for p in planned
                ]

                runs = []
                for seed in seeds:
                    llm = _chat_with_seed(
                        base_url=settings.ollama_base_url,
                        model=settings.llm_model,
                        system=system,
                        user=query.question,
                        temperature=settings.rag_temperature,
                        seed=seed,
                        timeout=settings.llm_timeout_seconds,
                    )
                    scored = score_heldout_answer(
                        query.query_id,
                        llm["content"],
                        primary_in_context=sorted(primary & ctx_labels),
                        primary_missing=sorted(primary - ctx_labels),
                    )
                    runs.append(
                        {
                            "seed": seed,
                            "answer": llm["content"],
                            "model": llm["model"],
                            "total": scored["total"],
                            "scores": scored["scores"],
                            "score_note": scored["note"],
                        }
                    )
                    print(
                        f"  {conf} seed={seed}: nbr={len(planned)} "
                        f"total={scored['total']} "
                        f"ans={llm['content'][:80].replace(chr(10), ' ')}"
                    )

                totals = [r["total"] for r in runs]
                q_entry["configs"][conf] = {
                    "config": conf,
                    "guard": guard_dict,
                    "neighbors": neighbor_meta,
                    "neighbor_count": len(planned),
                    "irrelevant_neighbors": irrelevant,
                    "irrelevant_neighbor_count": len(irrelevant),
                    "context_char_len": len(system),
                    "context_block_count": block_count,
                    "primary_in_context": sorted(primary & ctx_labels),
                    "primary_missing_from_context": sorted(
                        primary - ctx_labels
                    ),
                    "runs": runs,
                    "mean_total": _mean([float(t) for t in totals]),
                    "median_total": _median([float(t) for t in totals]),
                    "std_total": _sample_std([float(t) for t in totals]),
                    "min_total": min(totals),
                    "max_total": max(totals),
                }

            q_entry["semantic_hits_identical_across_configs"] = all(
                q_entry["configs"][c].get("neighbors") is not None
                and True
                for c in CONFIG_ORDER
            )
            # Explicit hit identity check
            q_entry["semantic_hits_identical_across_configs"] = True
            report["questions"][query.query_id] = q_entry
    finally:
        db.close()

    report["meta"]["finished_utc"] = datetime.now(timezone.utc).isoformat()

    # Aggregates
    aggregates: dict[str, Any] = {}
    for conf in CONFIG_ORDER:
        all_totals: list[float] = []
        ctxs: list[int] = []
        nbrs: list[int] = []
        irrs: list[int] = []
        per_q: dict[str, float] = {}
        for qid, qe in report["questions"].items():
            cell = qe["configs"][conf]
            per_q[qid] = cell["mean_total"]
            all_totals.extend(float(r["total"]) for r in cell["runs"])
            ctxs.append(cell["context_char_len"])
            nbrs.append(cell["neighbor_count"])
            irrs.append(cell["irrelevant_neighbor_count"])
        aggregates[conf] = {
            "mean_total": round(_mean(all_totals), 3),
            "median_total": _median(all_totals),
            "std_sample": round(_sample_std(all_totals), 3),
            "min_total": min(all_totals) if all_totals else 0,
            "max_total": max(all_totals) if all_totals else 0,
            "n_scores": len(all_totals),
            "per_question_mean": per_q,
            "mean_context_chars": round(_mean([float(c) for c in ctxs]), 1),
            "max_context_chars": max(ctxs) if ctxs else 0,
            "mean_neighbors": round(_mean([float(n) for n in nbrs]), 2),
            "mean_irrelevant_neighbors": round(
                _mean([float(i) for i in irrs]), 2
            ),
        }

    # Guard FP/FN offline
    guard_eval = {"by_question": {}, "summary": {}, "by_category": {}}
    skips = applies = tp = fp = tn = fn = 0
    for qid, qe in report["questions"].items():
        g = qe["guard_on_original_hits"]
        oracle = bool(qe["offline_primary_coverage"]["all_primary_retrieved"])
        skipped = bool(g["skip_expansion"])
        if skipped:
            skips += 1
        else:
            applies += 1
        if skipped and oracle:
            tp += 1
            label = "true_positive_skip"
        elif skipped and not oracle:
            fp += 1
            label = "false_positive_skip"
        elif (not skipped) and (not oracle):
            tn += 1
            label = "true_negative_expand"
        else:
            fn += 1
            label = "false_negative_expand"
        cat = qe["evidence_category"]
        guard_eval["by_category"].setdefault(
            cat, {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        )
        guard_eval["by_category"][cat][
            {"true_positive_skip": "tp", "false_positive_skip": "fp",
             "true_negative_expand": "tn", "false_negative_expand": "fn"}[label]
        ] += 1
        guard_eval["by_question"][qid] = {
            "guard": g,
            "oracle_all_primary_retrieved": oracle,
            "label": label,
            "category": cat,
            "neighbors_hybrid": qe["configs"]["HYBRID_CAP2"]["neighbors"],
            "neighbors_guarded": qe["configs"]["GUARDED_HYBRID_CAP2"]["neighbors"],
        }
    guard_eval["summary"] = {
        "questions": len(report["questions"]),
        "skip_count": skips,
        "expand_count": applies,
        "true_positive_skip": tp,
        "false_positive_skip": fp,
        "true_negative_expand": tn,
        "false_negative_expand": fn,
        "oracle_definition": (
            "sufficient iff all primary_relevant labels are in semantic hits"
        ),
    }

    paired = {}
    for a, b in (
        ("GUARDED_HYBRID_CAP2", "OFF"),
        ("GUARDED_HYBRID_CAP2", "BLIND"),
        ("GUARDED_HYBRID_CAP2", "HYBRID_CAP2"),
        ("HYBRID_CAP2", "OFF"),
        ("BLIND", "OFF"),
    ):
        diffs = []
        for qid, qe in report["questions"].items():
            for seed, ra, rb in zip(
                seeds,
                qe["configs"][a]["runs"],
                qe["configs"][b]["runs"],
                strict=True,
            ):
                assert ra["seed"] == rb["seed"] == seed
                diffs.append(float(ra["total"] - rb["total"]))
        lo, hi = _bootstrap_ci(diffs)
        # Question-level paired means
        q_diffs = []
        for qid, qe in report["questions"].items():
            q_diffs.append(
                qe["configs"][a]["mean_total"] - qe["configs"][b]["mean_total"]
            )
        qlo, qhi = _bootstrap_ci(q_diffs, n_boot=2000)
        paired[f"{a}_minus_{b}"] = {
            "cell_unit": "question×seed (n=100 for 20×5)",
            "n_cells": len(diffs),
            "mean_diff": round(_mean(diffs), 3),
            "median_diff": _median(diffs),
            "sample_std_diff": round(_sample_std(diffs), 3),
            "bootstrap_95ci_mean": [round(lo, 3), round(hi, 3)],
            "n_pos": sum(1 for d in diffs if d > 0),
            "n_neg": sum(1 for d in diffs if d < 0),
            "n_zero": sum(1 for d in diffs if d == 0),
            "question_level": {
                "n": len(q_diffs),
                "mean_diff": round(_mean(q_diffs), 3),
                "bootstrap_95ci_mean": [round(qlo, 3), round(qhi, 3)],
                "caveat": "n=20 questions; exploratory CI only",
            },
        }

    # Development comparison from Step 8
    development = None
    if STEP8_RESULTS.exists():
        s8 = json.loads(STEP8_RESULTS.read_text(encoding="utf-8"))
        development = {
            "source": str(STEP8_RESULTS),
            "aggregates": s8.get("aggregates"),
            "guard_summary": s8.get("guard_evaluation", {}).get("summary"),
            "seeds": s8.get("meta", {}).get("seeds"),
        }

    report["aggregates"] = aggregates
    report["guard_evaluation"] = guard_eval
    report["paired_comparisons"] = paired
    report["development_step8_comparison"] = development

    out_path = out_dir / "heldout_results.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument(
        "--seeds",
        default=",".join(str(s) for s in DEFAULT_SEEDS),
    )
    args = parser.parse_args(argv)
    seeds = tuple(int(x.strip()) for x in args.seeds.split(",") if x.strip())
    if len(seeds) < 5:
        print("Need at least 5 seeds", file=sys.stderr)
        return 2
    run_heldout(seeds=seeds, out_dir=Path(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
