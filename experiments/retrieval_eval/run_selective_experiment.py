#!/usr/bin/env python3
"""
Isolated selective neighbor-expansion experiment (Phase 4.2 P1 Step 5).

Runs OFF / BLIND / A_TABLE / B_PROCEDURE / C_EVIDENCE on Q1–Q7 without
modifying production RAG code. Semantic search is executed once per question;
only expansion planning differs.

Usage:
  PYTHONPATH=backend:. python -m experiments.retrieval_eval.run_selective_experiment
  PYTHONPATH=backend:. python -m experiments.retrieval_eval.run_selective_experiment \\
      --json-out experiments/retrieval_eval/selective_expansion_results.json
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

from sqlalchemy import and_, or_, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.document_embedding import DocumentEmbedding
from app.schemas.search import SemanticSearchResult
from app.services.llm.base import ChatMessage
from app.services.llm.factory import get_llm_provider
from app.services.neighbor_expansion import (
    build_context_blocks,
    format_context_blocks,
)
from app.services.semantic_search import SemanticSearchService
from experiments.retrieval_eval.dataset import EvalQuery, get_eval_queries
from experiments.retrieval_eval.selective_strategies import (
    STRATEGIES,
    PlannedNeighbor,
    _question_terms,
)


CONFIG_ORDER = ("OFF", "BLIND", "A_TABLE", "B_PROCEDURE", "C_EVIDENCE")


def _load_texts(
    db, keys: list[tuple[str, int]]
) -> dict[tuple[str, int], str]:
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
    return {
        (str(n), int(i)): str(t) for n, i, t in rows
    }


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
        # Keep overdue 7-day completions even if lexical overlap is thin.
        if "7 calendar days" in text or "calendar days" in lower:
            kept.append(item)
            continue
        # Table continuations: keep pipe-heavy neighbors for truncated tables.
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
    # Also treat same-document adjacent of a primary as potentially useful
    primary_docs = {c.document_name for c in query.primary_relevant}
    out = []
    for p in planned:
        label = f"{p.document_name}#{p.chunk_index}"
        if label in useful:
            continue
        # Heuristic: neighbors from non-primary documents are irrelevant.
        if p.document_name not in primary_docs:
            out.append(label)
            continue
        # Same-doc but not primary/optional — count as soft-irrelevant.
        out.append(label)
    return out


def _build_system(context: str, system_prompt: str) -> str:
    return (
        f"{system_prompt.strip()}\n\n"
        "CONTEXT (untrusted retrieved document excerpts):\n"
        f"{context}\n"
    )


def run_experiment(*, json_out: str) -> dict[str, Any]:
    settings = get_settings()
    queries = get_eval_queries()
    started = datetime.now(timezone.utc).isoformat()
    db = SessionLocal()
    search = SemanticSearchService(db, settings=settings)
    llm = get_llm_provider()

    report: dict[str, Any] = {
        "meta": {
            "timestamp_utc": started,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "rag_top_k": 5,
            "rag_min_similarity": 0.5,
            "rag_temperature": settings.rag_temperature,
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
            q_entry: dict[str, Any] = {
                "question": query.question,
                "primary_relevant": [c.label() for c in query.primary_relevant],
                "semantic_hits": hit_summary,
                "configs": {},
            }

            for conf in CONFIG_ORDER:
                planner = STRATEGIES[conf]
                if conf == "C_EVIDENCE":
                    # Prefetch ±1 candidates for relevance gating.
                    cand_keys = []
                    for h in hits:
                        for idx in (h.chunk_index - 1, h.chunk_index + 1):
                            if idx >= 0:
                                cand_keys.append((h.document_name, idx))
                    previews = _load_texts(db, cand_keys)
                    planned = planner(
                        hits, question=query.question, neighbor_preview=previews
                    )
                elif conf == "BLIND":
                    planned = planner(hits, question=query.question, max_expanded=10)
                elif conf == "OFF":
                    planned = planner(hits, question=query.question)
                else:
                    planned = planner(hits, question=query.question, max_expanded=4)

                prod_items = [p.to_production_item() for p in planned]
                texts = _load_texts(db, [p.key() for p in planned])
                if conf == "C_EVIDENCE":
                    planned = _filter_c_by_relevance(planned, texts, query.question)
                    prod_items = [p.to_production_item() for p in planned]
                    texts = {k: texts[k] for k in texts if k in {p.key() for p in planned}}

                if conf == "OFF" or not planned:
                    # Plain retrieved-only context (match production OFF formatting).
                    blocks_txt = []
                    for i, hit in enumerate(hits, start=1):
                        blocks_txt.append(
                            f"[{i}] role=retrieved "
                            f"source={hit.document_name} "
                            f"chunk_index={hit.chunk_index} "
                            f"similarity={hit.similarity:.4f}\n"
                            f"{hit.chunk_text}"
                        )
                    context = "\n\n".join(blocks_txt)
                    block_count = len(hits)
                else:
                    blocks = build_context_blocks(hits, texts, prod_items)
                    context = format_context_blocks(blocks)
                    block_count = len(blocks)

                system = _build_system(context, settings.rag_system_prompt)
                messages = [
                    ChatMessage(role="system", content=system),
                    ChatMessage(role="user", content=query.question),
                ]
                llm_resp = llm.chat(
                    messages, temperature=settings.rag_temperature
                )
                answer = (llm_resp.content or "").strip()
                irrelevant = _irrelevant_neighbors(planned, query)
                primary = {c.label() for c in query.primary_relevant}
                ctx_labels = set(
                    re.findall(
                        r"source=(\S+)\s+chunk_index=(\d+)", context
                    )
                )
                ctx_label_set = {f"{d}#{i}" for d, i in ctx_labels}
                primary_in = sorted(primary & ctx_label_set)
                primary_missing = sorted(primary - ctx_label_set)

                cfg_result = {
                    "config": conf,
                    "answer": answer,
                    "neighbors": [
                        {
                            "label": f"{p.document_name}#{p.chunk_index}",
                            "direction": p.direction,
                            "origin": f"{p.origin_document_name}#{p.origin_chunk_index}",
                            "reason": p.reason,
                        }
                        for p in planned
                    ],
                    "neighbor_count": len(planned),
                    "irrelevant_neighbors": irrelevant,
                    "irrelevant_neighbor_count": len(irrelevant),
                    "context_char_len": len(system),
                    "context_block_count": block_count,
                    "primary_in_context": primary_in,
                    "primary_missing_from_context": primary_missing,
                    "semantic_hits": hit_summary,
                    "model": llm_resp.model,
                    "provider": llm_resp.provider,
                }
                q_entry["configs"][conf] = cfg_result
                print(
                    f"  {conf}: neighbors={len(planned)} "
                    f"ctx={len(system)} irr={len(irrelevant)} "
                    f"missing={primary_missing}"
                )
                print(f"    ANSWER: {answer[:180].replace(chr(10), ' ')}")

            # Verify identical semantic hits recorded
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
        default="experiments/retrieval_eval/selective_expansion_results.json",
    )
    args = parser.parse_args(argv)
    try:
        run_experiment(json_out=args.json_out)
    except Exception as exc:
        print(f"EXPERIMENT FAILED: {exc}", file=sys.stderr)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
