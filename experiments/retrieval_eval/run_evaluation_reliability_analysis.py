#!/usr/bin/env python3
"""
Step 7 — evaluation reliability / paired statistical analysis (read-only).

Reads hybrid_expansion_stability_scores.json + results; writes
evaluation_reliability_stats.json. Does not modify scores or production code.

Usage:
  python -m experiments.retrieval_eval.run_evaluation_reliability_analysis
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    if n % 2:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2


def pstdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def sample_std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def cohens_dz(diffs: list[float]) -> float | None:
    sd = sample_std(diffs)
    if sd == 0:
        return None
    return mean(diffs) / sd


def bootstrap_mean_ci(
    diffs: list[float],
    *,
    n_boot: int = 5000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(diffs)
    means: list[float] = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(mean(sample))
    means.sort()
    lo = means[int(alpha / 2 * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot) - 1]
    return lo, hi


def sign_summary(diffs: list[float]) -> dict[str, int]:
    nz = [d for d in diffs if d != 0]
    return {
        "n": len(diffs),
        "n_zero": len(diffs) - len(nz),
        "n_pos": sum(1 for d in nz if d > 0),
        "n_neg": sum(1 for d in nz if d < 0),
    }


def main() -> int:
    base = Path("experiments/retrieval_eval")
    res = json.loads(
        (base / "hybrid_expansion_stability_results.json").read_text(
            encoding="utf-8"
        )
    )
    sc = json.loads(
        (base / "hybrid_expansion_stability_scores.json").read_text(
            encoding="utf-8"
        )
    )
    configs = list(res["meta"]["configs"])
    seeds = list(res["meta"]["seeds"])
    qs = list(res["questions"])

    scores: dict[tuple[str, int, str], int] = {}
    for q in qs:
        for conf in configs:
            for r in sc["per_run"][q][conf]["runs"]:
                scores[(q, int(r["seed"]), conf)] = int(r["total"])

    descriptive: dict[str, Any] = {}
    for conf in configs:
        vals = [float(scores[(q, s, conf)]) for q in qs for s in seeds]
        descriptive[conf] = {
            "n": len(vals),
            "mean": round(mean(vals), 3),
            "median": median(vals),
            "std_population": round(pstdev(vals), 3),
            "std_sample": round(sample_std(vals), 3),
            "min": min(vals),
            "max": max(vals),
            "note": (
                "n=21 = 7 questions × 3 seeds; observations within a question "
                "share retrieval/context and are not independent."
            ),
        }

    per_question: dict[str, Any] = {}
    for q in qs:
        per_question[q] = {}
        for conf in configs:
            vals = [float(scores[(q, s, conf)]) for s in seeds]
            per_question[q][conf] = {
                "values": vals,
                "mean": round(mean(vals), 3),
                "std_population": round(pstdev(vals), 3),
            }

    def paired(a: str, b: str) -> list[float]:
        return [
            float(scores[(q, s, a)] - scores[(q, s, b)])
            for q in qs
            for s in seeds
        ]

    pair_names = [
        ("BLIND", "OFF"),
        ("HYBRID_CAP2", "OFF"),
        ("HYBRID_CAP2", "BLIND"),
        ("HYBRID_CAP2", "C_EVIDENCE"),
        ("HYBRID_CAP2", "A_TABLE"),
        ("C_EVIDENCE", "BLIND"),
        ("HYBRID_CAP3", "HYBRID_CAP2"),
        ("A_TABLE", "OFF"),
    ]
    paired_cell: dict[str, Any] = {}
    for a, b in pair_names:
        d = paired(a, b)
        lo, hi = bootstrap_mean_ci(d)
        dz = cohens_dz(d)
        paired_cell[f"{a}_minus_{b}"] = {
            "unit": "matched (question, seed) cell",
            "n": len(d),
            "mean_diff": round(mean(d), 3),
            "median_diff": median(d),
            "sample_std_diff": round(sample_std(d), 3),
            "cohens_dz": None if dz is None else round(dz, 3),
            "bootstrap_95ci_mean": [round(lo, 3), round(hi, 3)],
            "sign_counts": sign_summary(d),
            "caveat": (
                "Cells share question-level retrieval/context; treat CI as "
                "descriptive, not confirmatory significance."
            ),
        }

    paired_question: dict[str, Any] = {}
    for a, b in [
        ("BLIND", "OFF"),
        ("HYBRID_CAP2", "OFF"),
        ("HYBRID_CAP2", "BLIND"),
        ("C_EVIDENCE", "BLIND"),
        ("HYBRID_CAP2", "C_EVIDENCE"),
    ]:
        d = []
        per_q = {}
        for q in qs:
            ma = mean([float(scores[(q, s, a)]) for s in seeds])
            mb = mean([float(scores[(q, s, b)]) for s in seeds])
            delta = ma - mb
            d.append(delta)
            per_q[q] = round(delta, 3)
        lo, hi = bootstrap_mean_ci(d, n_boot=2000)
        dz = cohens_dz(d)
        paired_question[f"{a}_minus_{b}"] = {
            "unit": "question-mean (n=7)",
            "n": len(d),
            "mean_diff": round(mean(d), 3),
            "median_diff": round(median(d), 3),
            "sample_std_diff": round(sample_std(d), 3),
            "cohens_dz": None if dz is None else round(dz, 3),
            "bootstrap_95ci_mean": [round(lo, 3), round(hi, 3)],
            "per_question_delta": per_q,
            "caveat": (
                "n=7 is too small for confirmatory inference; "
                "Q6 can dominate the mean."
            ),
        }

    q6 = res["questions"]["Q6"]
    q6_invest = {
        "semantic_hits": q6["semantic_hits"],
        "configs": {},
    }
    for conf in configs:
        c = q6["configs"][conf]
        q6_invest["configs"][conf] = {
            "neighbors": c["neighbors"],
            "neighbor_count": c["neighbor_count"],
            "irrelevant_neighbors": c["irrelevant_neighbors"],
            "primary_in_context": c["primary_in_context"],
            "primary_missing_from_context": c["primary_missing_from_context"],
            "context_char_len": c["context_char_len"],
            "answers": [
                {
                    "seed": r["seed"],
                    "total": scores[("Q6", int(r["seed"]), conf)],
                    "answer": r["answer"],
                }
                for r in c["runs"]
            ],
        }

    out = {
        "meta": {
            "source_results": str(base / "hybrid_expansion_stability_results.json"),
            "source_scores": str(base / "hybrid_expansion_stability_scores.json"),
            "seeds": seeds,
            "configs": configs,
            "analysis": "descriptive + paired bootstrap CIs; no p-value claims",
        },
        "descriptive": descriptive,
        "per_question": per_question,
        "paired_cell_level": paired_cell,
        "paired_question_level": paired_question,
        "q6_investigation_snapshot": q6_invest,
    }
    out_path = base / "evaluation_reliability_stats.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    for conf, d in descriptive.items():
        print(f"{conf}: mean={d['mean']} sd={d['std_population']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
