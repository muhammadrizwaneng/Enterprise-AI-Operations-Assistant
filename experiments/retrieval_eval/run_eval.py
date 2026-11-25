#!/usr/bin/env python3
"""
Live retrieval evaluation harness (Phase 4.2 P1 Step 2A).

Calls the existing ``POST /api/v1/search/semantic`` endpoint. Does not
reimplement ranking, modify production defaults, or write to the database.

Usage
-----
    PYTHONPATH=backend:. python -m experiments.retrieval_eval.run_eval
    PYTHONPATH=backend:. python -m experiments.retrieval_eval.run_eval \\
        --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import httpx

from experiments.retrieval_eval.dataset import (
    EVAL_CONFIGS,
    EvalQuery,
    get_eval_queries,
)
from experiments.retrieval_eval.metrics import (
    AggregateMetrics,
    QueryMetrics,
    RetrievedChunk,
    evaluate_query,
    evaluate_run,
)


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
SEARCH_PATH = "/api/v1/search/semantic"


class EvaluationError(RuntimeError):
    """Raised when the evaluation harness cannot reach search."""


def _parse_hits(payload: dict[str, Any]) -> list[RetrievedChunk]:
    results = payload.get("results")
    if results is None:
        raise EvaluationError("Search response missing 'results'")
    hits: list[RetrievedChunk] = []
    for item in results:
        hits.append(
            RetrievedChunk(
                document_name=str(item["document_name"]),
                chunk_index=int(item["chunk_index"]),
                similarity=float(item["similarity"]),
            )
        )
    return hits


def search_via_api(
    client: httpx.Client,
    *,
    base_url: str,
    question: str,
    top_k: int,
    min_similarity: float,
) -> list[RetrievedChunk]:
    url = base_url.rstrip("/") + SEARCH_PATH
    try:
        response = client.post(
            url,
            json={
                "query": question,
                "top_k": top_k,
                "min_similarity": min_similarity,
            },
        )
    except httpx.ConnectError as exc:
        raise EvaluationError(
            f"Cannot connect to semantic search at {url}. "
            "Is FastAPI running?"
        ) from exc
    except httpx.TimeoutException as exc:
        raise EvaluationError(
            f"Timed out calling semantic search at {url}"
        ) from exc
    except httpx.HTTPError as exc:
        raise EvaluationError(f"HTTP error calling {url}: {exc}") from exc

    if response.status_code != 200:
        detail = response.text[:500]
        raise EvaluationError(
            f"Semantic search returned HTTP {response.status_code}: {detail}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise EvaluationError(
            "Semantic search returned non-JSON body"
        ) from exc
    return _parse_hits(payload)


def evaluate_config(
    *,
    client: httpx.Client,
    base_url: str,
    queries: tuple[EvalQuery, ...],
    top_k: int,
    min_similarity: float,
) -> tuple[list[QueryMetrics], AggregateMetrics]:
    per_query: list[QueryMetrics] = []
    for query in queries:
        try:
            hits = search_via_api(
                client,
                base_url=base_url,
                question=query.question,
                top_k=top_k,
                min_similarity=min_similarity,
            )
            per_query.append(
                evaluate_query(
                    query,
                    hits,
                    retrieval_top_k=top_k,
                )
            )
        except EvaluationError as exc:
            per_query.append(
                evaluate_query(
                    query,
                    [],
                    retrieval_top_k=top_k,
                    error=str(exc),
                )
            )
    return per_query, evaluate_run(per_query)


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _print_query(metrics: QueryMetrics, *, top_k: int) -> None:
    print(f"\n--- {metrics.query_id} ---")
    print(f"Question: {metrics.question}")
    print(f"Expected primary: {', '.join(metrics.primary_relevant)}")
    if metrics.error:
        print(f"ERROR: {metrics.error}")
        return
    print(f"Result count: {metrics.result_count}")
    print(f"First relevant rank: {metrics.first_relevant_rank}")
    print(f"Missing relevant: {metrics.missing_relevant or '[]'}")
    print(
        f"Recall@5={_fmt(metrics.recall_at_5)}  "
        f"Recall@10={_fmt(metrics.recall_at_10)}  "
        f"Precision@5={_fmt(metrics.precision_at_5)}  "
        f"MRR={_fmt(metrics.mrr)}  "
        f"source_hit={metrics.source_hit}"
    )
    show_n = min(len(metrics.retrieved), max(top_k, 10))
    print(f"Retrieved (showing up to {show_n}):")
    for i, hit in enumerate(metrics.retrieved[:show_n], start=1):
        print(
            f"  {i:2d}. {hit['label']}  "
            f"sim={float(hit['similarity']):.4f}"
        )


def _print_aggregate(name: str, aggregate: AggregateMetrics) -> None:
    print(f"\n=== AGGREGATE ({name}) ===")
    print(f"Queries scored: {aggregate.scored_query_count}/{aggregate.query_count}")
    if aggregate.skipped_query_ids:
        print(f"Skipped: {aggregate.skipped_query_ids}")
    print(f"Mean Recall@5:      {_fmt(aggregate.mean_recall_at_5)}")
    print(f"Mean Recall@10:     {_fmt(aggregate.mean_recall_at_10)}")
    print(f"Mean Precision@5:   {_fmt(aggregate.mean_precision_at_5)}")
    print(f"Mean MRR:           {_fmt(aggregate.mean_mrr)}")
    print(f"Source coverage:    {_fmt(aggregate.source_coverage)}")


def _print_focus(results: list[QueryMetrics], *, top_k: int) -> None:
    print("\n=== DETAILED FOCUS: Q1 / Q2 / Q3 ===")
    focus = {q.query_id: q for q in results if q.query_id in {"Q1", "Q2", "Q3"}}
    for qid in ("Q1", "Q2", "Q3"):
        item = focus.get(qid)
        if item is None:
            print(f"\n{qid}: missing from results")
            continue
        _print_query(item, top_k=top_k)


def run(
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 120.0,
) -> dict[str, Any]:
    queries = get_eval_queries()
    started = datetime.now(timezone.utc)
    environment = {
        "base_url": base_url,
        "search_path": SEARCH_PATH,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "timestamp_utc": started.isoformat(),
    }

    # Health check first for a clear error message.
    health_url = base_url.rstrip("/") + "/health"
    try:
        with httpx.Client(timeout=timeout) as probe:
            health = probe.get(health_url)
    except httpx.HTTPError as exc:
        raise EvaluationError(
            f"API unavailable at {health_url}: {exc}"
        ) from exc
    if health.status_code != 200:
        raise EvaluationError(
            f"Health check failed at {health_url}: HTTP {health.status_code}"
        )

    report: dict[str, Any] = {
        "environment": environment,
        "configs": {},
    }

    with httpx.Client(timeout=timeout) as client:
        for config in EVAL_CONFIGS:
            name = str(config["name"])
            top_k = int(config["top_k"])
            min_similarity = float(config["min_similarity"])
            print("\n" + "=" * 72)
            print(f"CONFIG: {name} ({config['description']})")
            print(f"top_k={top_k}  min_similarity={min_similarity}")
            print(f"timestamp_utc={environment['timestamp_utc']}")
            print("=" * 72)

            per_query, aggregate = evaluate_config(
                client=client,
                base_url=base_url,
                queries=queries,
                top_k=top_k,
                min_similarity=min_similarity,
            )
            for item in per_query:
                _print_query(item, top_k=top_k)
            _print_aggregate(name, aggregate)
            _print_focus(per_query, top_k=top_k)

            report["configs"][name] = {
                "top_k": top_k,
                "min_similarity": min_similarity,
                "description": config["description"],
                "queries": [asdict(q) for q in per_query],
                "aggregate": asdict(aggregate),
            }

    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Phase 4.2 P1 retrieval evaluation baseline"
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"FastAPI base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write the full JSON report",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP timeout seconds (default: 120)",
    )
    args = parser.parse_args(argv)

    try:
        report = run(base_url=args.base_url, timeout=args.timeout)
    except EvaluationError as exc:
        print(f"EVALUATION FAILED: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        print(f"\nWrote JSON report to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
