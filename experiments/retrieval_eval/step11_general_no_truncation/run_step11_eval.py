#!/usr/bin/env python3
"""
Step 11 — GENERAL truncation ablation eval (H2: Q28–Q47).

Configs: OFF, BLIND, HYBRID_CAP2, GENERAL_NO_TRUNCATION.
Does not modify production RAG, evidence_guard.py, or prior step artifacts.

Usage:
  PYTHONPATH=backend:. python -m experiments.retrieval_eval.step11_general_no_truncation.run_step11_eval
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
)
from experiments.retrieval_eval.selective_strategies import (
    PlannedNeighbor,
    _chunk_truncated,
    _procedure_needs_next,
    _question_terms,
    _table_appears_incomplete,
    plan_blind,
    plan_hybrid,
    plan_off,
)
from experiments.retrieval_eval.step11_general_no_truncation.general_no_truncation_guard import (
    assess_evidence_sufficiency_no_general_truncation,
    plan_general_no_truncation,
)
from experiments.retrieval_eval.step11_general_no_truncation.h2_dataset import (
    get_h2_queries,
)
from experiments.retrieval_eval.step11_general_no_truncation.h2_scoring import (
    score_h2_answer,
)


DEFAULT_SEEDS = (101, 202, 303, 404, 505)
CONFIG_ORDER = ("OFF", "BLIND", "HYBRID_CAP2", "GENERAL_NO_TRUNCATION")
OUT_DIR = Path(
    "experiments/retrieval_eval/step11_general_no_truncation/results"
)
GUARD_PATH = Path("experiments/retrieval_eval/evidence_guard.py")
EXPECTED_GUARD_SHA256 = (
    "4ab51eb2ad25a7ece5062878ae713c4537df54368ee9324139b891fbaf11eae6"
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
    if conf == "GENERAL_NO_TRUNCATION":
        planned, guard = plan_general_no_truncation(
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


def _incompleteness_breakdown(hits) -> dict[str, Any]:
    trunc = sum(1 for h in hits if _chunk_truncated(h.chunk_text))
    tab = sum(1 for h in hits if _table_appears_incomplete(h.chunk_text))
    proc = sum(1 for h in hits if _procedure_needs_next(h.chunk_text))
    trunc_only = sum(
        1
        for h in hits
        if _chunk_truncated(h.chunk_text)
        and not _table_appears_incomplete(h.chunk_text)
        and not _procedure_needs_next(h.chunk_text)
    )
    return {
        "hits_truncated": trunc,
        "hits_table_incomplete": tab,
        "hits_procedure_needs_next": proc,
        "hits_truncation_only": trunc_only,
        "any_truncation": trunc > 0,
        "any_table_or_procedure": (tab + proc) > 0,
    }


def run_step11(*, seeds: tuple[int, ...], out_dir: Path) -> dict[str, Any]:
    guard_hash = _sha256_file(GUARD_PATH)
    if guard_hash != EXPECTED_GUARD_SHA256:
        raise RuntimeError(
            "Frozen guard hash mismatch. Step 11 forbids modifying "
            f"evidence_guard.py. expected={EXPECTED_GUARD_SHA256} got={guard_hash}"
        )

    settings = get_settings()
    h2 = get_h2_queries()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    db = SessionLocal()
    search = SemanticSearchService(db, settings=settings)

    report: dict[str, Any] = {
        "meta": {
            "experiment": "step11_general_truncation_ablation",
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
            "dataset": "H2 Q28–Q47 (independent of Q1–Q27)",
            "frozen_guard_sha256": guard_hash,
            "ablation": (
                "GENERAL path ignores _chunk_truncated only; "
                "specialized needs and HYBRID_CAP2 planner unchanged"
            ),
            "note": (
                "Answer key used offline for scoring only. "
                "Frozen guard decisions logged diagnostically; "
                "not a scored config."
            ),
        },
        "questions": {},
    }

    try:
        for item in h2:
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
            frozen_guard = assess_evidence_sufficiency(query.question, hits)
            abl_guard = assess_evidence_sufficiency_no_general_truncation(
                query.question, hits
            )
            incompleteness = _incompleteness_breakdown(hits)

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
                "expects_neighbor_helpful": item.expects_neighbor_helpful,
                "notes": item.notes,
                "primary_relevant": sorted(primary),
                "semantic_hits": hit_summary,
                "offline_primary_coverage": offline_cov,
                "incompleteness_breakdown": incompleteness,
                "frozen_guard_diagnostic": frozen_guard.to_dict(),
                "ablation_guard_on_hits": abl_guard.to_dict(),
                "configs": {},
            }

            for conf in CONFIG_ORDER:
                planned, guard_dict = _plan(
                    conf, hits, question=query.question, previews=previews
                )
                texts = _load_texts(db, [p.key() for p in planned])
                if conf in ("HYBRID_CAP2", "GENERAL_NO_TRUNCATION") and planned:
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
                irrelevant = [
                    f"{p.document_name}#{p.chunk_index}"
                    for p in planned
                    if f"{p.document_name}#{p.chunk_index}" not in primary
                ]
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
                    scored = score_h2_answer(
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
                            "facts_hit": scored["facts_hit"],
                            "facts_total": scored["facts_total"],
                            "groups_ok": scored["groups_ok"],
                        }
                    )
                    print(
                        f"  {conf} seed={seed}: nbr={len(planned)} "
                        f"total={scored['total']} "
                        f"ans={llm['content'][:80].replace(chr(10), ' ')}"
                    )

                totals = [r["total"] for r in runs]
                completeness = [
                    float(r["scores"]["completeness"]) for r in runs
                ]
                unsupported = [
                    float(r["scores"]["unsupported_claims"]) for r in runs
                ]
                correctness = [
                    float(r["scores"]["correctness"]) for r in runs
                ]
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
                    "mean_completeness": _mean(completeness),
                    "mean_correctness": _mean(correctness),
                    "mean_unsupported_claims": _mean(unsupported),
                }

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
        skips = 0
        per_q: dict[str, float] = {}
        comp: list[float] = []
        corr: list[float] = []
        uns: list[float] = []
        for qid, qe in report["questions"].items():
            cell = qe["configs"][conf]
            per_q[qid] = cell["mean_total"]
            all_totals.extend(float(r["total"]) for r in cell["runs"])
            ctxs.append(cell["context_char_len"])
            nbrs.append(cell["neighbor_count"])
            irrs.append(cell["irrelevant_neighbor_count"])
            if cell["neighbor_count"] == 0 and conf != "OFF":
                skips += 1
            elif conf == "GENERAL_NO_TRUNCATION" and (
                cell.get("guard") or {}
            ).get("skip_expansion"):
                skips += 1
            comp.append(cell["mean_completeness"])
            corr.append(cell["mean_correctness"])
            uns.append(cell["mean_unsupported_claims"])
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
            "expansion_skip_count": skips,
            "expansion_skip_rate": round(
                skips / max(1, len(report["questions"])), 3
            ),
            "mean_completeness": round(_mean(comp), 3),
            "mean_correctness": round(_mean(corr), 3),
            "mean_unsupported_claims": round(_mean(uns), 3),
        }

    # Slice by expects_neighbor_helpful
    slices: dict[str, Any] = {}
    for label, pred in (
        ("expects_neighbor_helpful", lambda qe: qe["expects_neighbor_helpful"]),
        (
            "original_evidence_sufficient_annotation",
            lambda qe: not qe["expects_neighbor_helpful"],
        ),
    ):
        qids = [qid for qid, qe in report["questions"].items() if pred(qe)]
        slice_agg = {}
        for conf in CONFIG_ORDER:
            totals = []
            for qid in qids:
                totals.extend(
                    float(r["total"])
                    for r in report["questions"][qid]["configs"][conf]["runs"]
                )
            slice_agg[conf] = {
                "n_questions": len(qids),
                "query_ids": qids,
                "mean_total": round(_mean(totals), 3),
                "n_scores": len(totals),
            }
        slices[label] = slice_agg

    # Guard ablation diagnostic (frozen vs ablation skip)
    abl_diag = {"by_question": {}, "summary": {}}
    frozen_skips = abl_skips = diverge = 0
    trunc_only_qs = 0
    for qid, qe in report["questions"].items():
        fs = bool(qe["frozen_guard_diagnostic"]["skip_expansion"])
        as_ = bool(qe["ablation_guard_on_hits"]["skip_expansion"])
        if fs:
            frozen_skips += 1
        if as_:
            abl_skips += 1
        if fs != as_:
            diverge += 1
        if (
            qe["incompleteness_breakdown"]["any_truncation"]
            and not qe["incompleteness_breakdown"]["any_table_or_procedure"]
        ):
            trunc_only_qs += 1
        abl_diag["by_question"][qid] = {
            "frozen_skip": fs,
            "ablation_skip": as_,
            "diverged": fs != as_,
            "need_frozen": qe["frozen_guard_diagnostic"]["need"],
            "need_ablation": qe["ablation_guard_on_hits"]["need"],
            "incompleteness": qe["incompleteness_breakdown"],
            "expects_neighbor_helpful": qe["expects_neighbor_helpful"],
            "neighbors_hybrid": qe["configs"]["HYBRID_CAP2"]["neighbors"],
            "neighbors_ablation": qe["configs"]["GENERAL_NO_TRUNCATION"][
                "neighbors"
            ],
        }
    abl_diag["summary"] = {
        "questions": len(report["questions"]),
        "frozen_skip_count": frozen_skips,
        "ablation_skip_count": abl_skips,
        "skip_decision_divergences": diverge,
        "questions_with_truncation_only_incompleteness": trunc_only_qs,
        "note": (
            "Divergence count isolates the effect of removing "
            "_chunk_truncated from GENERAL sufficiency."
        ),
    }

    paired = {}
    for a, b in (
        ("GENERAL_NO_TRUNCATION", "OFF"),
        ("GENERAL_NO_TRUNCATION", "BLIND"),
        ("GENERAL_NO_TRUNCATION", "HYBRID_CAP2"),
        ("HYBRID_CAP2", "OFF"),
        ("BLIND", "OFF"),
        ("BLIND", "HYBRID_CAP2"),
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
        q_diffs = [
            qe["configs"][a]["mean_total"] - qe["configs"][b]["mean_total"]
            for qe in report["questions"].values()
        ]
        qlo, qhi = _bootstrap_ci(q_diffs, n_boot=2000)
        paired[f"{a}_minus_{b}"] = {
            "cell_unit": f"question×seed (n={len(diffs)})",
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
                "caveat": "exploratory CI; small n",
            },
        }

    report["aggregates"] = aggregates
    report["slices"] = slices
    report["ablation_diagnostic"] = abl_diag
    report["paired_comparisons"] = paired

    out_path = out_dir / "step11_results.json"
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
    run_step11(seeds=seeds, out_dir=Path(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
