#!/usr/bin/env python3
"""
Isolated hybrid + multi-seed stability experiment (Phase 4.2 P1 Step 6).

Compares OFF / BLIND / A_TABLE / C_EVIDENCE / HYBRID_CAP2 / HYBRID_CAP3
across documented Ollama seeds. Production RAG / neighbor expansion untouched.

Ollama seed: production OllamaProvider does NOT expose seed. This harness calls
``/api/chat`` directly with ``options.seed`` (experiment-only). Seed control was
verified against the local Ollama server before the run.

Usage:
  PYTHONPATH=backend:. python -m experiments.retrieval_eval.run_hybrid_stability_experiment
"""

from __future__ import annotations

import argparse
import json
import platform
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
from experiments.retrieval_eval.dataset import EvalQuery, get_eval_queries
from experiments.retrieval_eval.selective_strategies import (
    PlannedNeighbor,
    _question_terms,
    plan_blind,
    plan_evidence_completion,
    plan_hybrid,
    plan_off,
    plan_table_aware,
)


# Prefer 3 documented seeds (verified deterministic). Cap configs as separate arms.
DEFAULT_SEEDS = (101, 202, 303)
CONFIG_ORDER = (
    "OFF",
    "BLIND",
    "A_TABLE",
    "C_EVIDENCE",
    "HYBRID_CAP2",
    "HYBRID_CAP3",
)


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
    """Same post-load relevance gate as Step 5 C_EVIDENCE."""
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


def _useful_labels(query: EvalQuery) -> set[str]:
    labels = {c.label() for c in query.primary_relevant}
    labels |= {c.label() for c in query.optional_supporting}
    return labels


def _irrelevant_neighbors(
    planned: list[PlannedNeighbor], query: EvalQuery
) -> list[str]:
    useful = _useful_labels(query)
    primary_docs = {c.document_name for c in query.primary_relevant}
    out: list[str] = []
    for p in planned:
        label = f"{p.document_name}#{p.chunk_index}"
        if label in useful:
            continue
        if p.document_name not in primary_docs:
            out.append(label)
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
    """Experiment-only Ollama call with options.seed (not via production provider)."""
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
        "raw_done_reason": data.get("done_reason"),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
    }


def _plan_for_config(
    conf: str,
    hits,
    *,
    question: str,
    previews: dict[tuple[str, int], str],
) -> list[PlannedNeighbor]:
    if conf == "OFF":
        return plan_off(hits, question=question)
    if conf == "BLIND":
        return plan_blind(hits, question=question, max_expanded=10)
    if conf == "A_TABLE":
        return plan_table_aware(hits, question=question, max_expanded=4)
    if conf == "C_EVIDENCE":
        return plan_evidence_completion(
            hits,
            question=question,
            neighbor_preview=previews,
            max_expanded=4,
        )
    if conf in ("HYBRID_CAP2", "HYBRID_CAP3"):
        # Over-fetch candidates; hard cap applied after relevance filter.
        return plan_hybrid(
            hits,
            question=question,
            neighbor_preview=previews,
            max_expanded=8,
        )
    raise ValueError(f"Unknown config: {conf}")


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


def run_experiment(
    *,
    json_out: str,
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    settings = get_settings()
    queries = get_eval_queries()
    started = datetime.now(timezone.utc).isoformat()
    db = SessionLocal()
    search = SemanticSearchService(db, settings=settings)

    report: dict[str, Any] = {
        "meta": {
            "experiment": "hybrid_expansion_stability_step6",
            "timestamp_utc": started,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "rag_top_k": 5,
            "rag_min_similarity": 0.5,
            "rag_temperature": settings.rag_temperature,
            "seeds": list(seeds),
            "seed_control": (
                "Experiment-only Ollama options.seed via direct /api/chat. "
                "Production OllamaProvider does not pass seed."
            ),
            "configs": list(CONFIG_ORDER),
            "note": "Isolated experiment; production neighbor expansion untouched",
        },
        "questions": {},
    }

    try:
        for query in queries:
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

            # Prefetch ±1 for C/HYBRID relevance gating (once per question).
            cand_keys: list[tuple[str, int]] = []
            for h in hits:
                for idx in (h.chunk_index - 1, h.chunk_index + 1):
                    if idx >= 0:
                        cand_keys.append((h.document_name, idx))
            previews = _load_texts(db, cand_keys)

            q_entry: dict[str, Any] = {
                "question": query.question,
                "primary_relevant": [c.label() for c in query.primary_relevant],
                "semantic_hits": hit_summary,
                "configs": {},
            }

            for conf in CONFIG_ORDER:
                planned = _plan_for_config(
                    conf, hits, question=query.question, previews=previews
                )
                texts = _load_texts(db, [p.key() for p in planned])
                if conf in ("C_EVIDENCE", "HYBRID_CAP2", "HYBRID_CAP3"):
                    planned = _filter_c_by_relevance(
                        planned, texts, query.question
                    )
                    if conf == "HYBRID_CAP2":
                        planned = planned[:2]
                    elif conf == "HYBRID_CAP3":
                        planned = planned[:3]
                    texts = {
                        k: texts[k]
                        for k in texts
                        if k in {p.key() for p in planned}
                    }

                if conf == "HYBRID_CAP2":
                    cap_ok = len(planned) <= 2
                elif conf == "HYBRID_CAP3":
                    cap_ok = len(planned) <= 3
                else:
                    cap_ok = True

                context, block_count = _format_context(hits, planned, texts)
                system = _build_system(context, settings.rag_system_prompt)
                irrelevant = _irrelevant_neighbors(planned, query)
                primary = {c.label() for c in query.primary_relevant}
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

                runs: list[dict[str, Any]] = []
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
                    runs.append(
                        {
                            "seed": seed,
                            "answer": llm["content"],
                            "model": llm["model"],
                            "prompt_eval_count": llm["prompt_eval_count"],
                            "eval_count": llm["eval_count"],
                        }
                    )
                    print(
                        f"  {conf} seed={seed}: nbr={len(planned)} "
                        f"ctx={len(system)} "
                        f"ans={llm['content'][:100].replace(chr(10), ' ')}"
                    )

                unique_answers = {r["answer"] for r in runs}
                q_entry["configs"][conf] = {
                    "config": conf,
                    "neighbors": neighbor_meta,
                    "neighbor_count": len(planned),
                    "cap_respected": cap_ok,
                    "irrelevant_neighbors": irrelevant,
                    "irrelevant_neighbor_count": len(irrelevant),
                    "context_char_len": len(system),
                    "context_block_count": block_count,
                    "primary_in_context": sorted(primary & ctx_labels),
                    "primary_missing_from_context": sorted(
                        primary - ctx_labels
                    ),
                    "semantic_hits": hit_summary,
                    "runs": runs,
                    "unique_answer_count_across_seeds": len(unique_answers),
                    "answers_identical_across_seeds": len(unique_answers) == 1,
                }

            q_entry["semantic_hits_identical_across_configs"] = all(
                q_entry["configs"][c]["semantic_hits"] == hit_summary
                for c in CONFIG_ORDER
            )
            report["questions"][query.query_id] = q_entry
    finally:
        db.close()

    report["meta"]["finished_utc"] = datetime.now(timezone.utc).isoformat()
    Path(json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {json_out}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=(
            "experiments/retrieval_eval/hybrid_expansion_stability_results.json"
        ),
    )
    parser.add_argument(
        "--seeds",
        default=",".join(str(s) for s in DEFAULT_SEEDS),
        help="Comma-separated integer seeds (default: 101,202,303)",
    )
    args = parser.parse_args(argv)
    seeds = tuple(int(x.strip()) for x in args.seeds.split(",") if x.strip())
    if len(seeds) < 3:
        print("Need at least 3 seeds", file=sys.stderr)
        return 2
    run_experiment(json_out=args.json_out, seeds=seeds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
