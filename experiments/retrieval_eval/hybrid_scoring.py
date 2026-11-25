"""
Checklist-assisted answer scoring for Step 6 (same Step 3 rubric).

Not an LLM judge. Scores from fixed evidence checklists + answer inspection
rules aligned with ANSWER_LEVEL_EVALUATION_REPORT.md.

Metric scale 0–4; unsupported_claims: higher = fewer unsupported claims.
Total per answer = sum of seven metrics (max 28).
"""

from __future__ import annotations

import re
from typing import Any


METRICS = (
    "correctness",
    "completeness",
    "evidence_utilization",
    "unsupported_claims",
    "conditions_exceptions",
    "relevance",
    "source_consistency",
)


def _has(text: str, *needles: str) -> bool:
    lower = text.lower()
    return all(n.lower() in lower for n in needles)


def _any(text: str, *needles: str) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles)


def _clamp(n: int) -> int:
    return max(0, min(4, n))


def score_answer(
    query_id: str,
    answer: str,
    *,
    primary_in_context: list[str],
    primary_missing: list[str],
    neighbor_labels: list[str],
) -> dict[str, Any]:
    """
    Return metric scores + notes for one answer.

    Uses question-specific evidence checklists from prior Step 3/4/5 analysis.
    """
    a = answer or ""
    missing = set(primary_missing)
    in_ctx = set(primary_in_context)

    if query_id == "Q1":
        # Align with Step 5: methods table + processing 1–2 + 15:00 cutoff.
        # "Expedited" accepted as Express synonym in live answers.
        methods = (
            _any(a, "standard ground")
            and _any(a, "3–7", "3-7")
            and _any(a, "express", "expedited")
            and _any(a, "overnight")
        )
        only_sg = _any(a, "standard ground") and _any(a, "3–7", "3-7") and not methods
        processing = _any(a, "1–2", "1-2") and _any(a, "processing", "warehouse")
        cutoff = _any(a, "15:00")
        fab = _any(a, "contact us form") and "ticket" not in a.lower()
        if methods and processing and cutoff:
            scores = {
                "correctness": 4,
                "completeness": 4,
                "evidence_utilization": 4,
                "unsupported_claims": 4,
                "conditions_exceptions": 4,
                "relevance": 4,
                "source_consistency": 4,
            }
        elif methods and cutoff:
            # Step5 C pattern (~25): methods + 15:00, miss processing.
            scores = {
                "correctness": 4,
                "completeness": 3,
                "evidence_utilization": 3,
                "unsupported_claims": 4,
                "conditions_exceptions": 3,
                "relevance": 4,
                "source_consistency": 4,
            }
        elif methods and not cutoff:
            scores = {
                "correctness": 3,
                "completeness": 2,
                "evidence_utilization": 2,
                "unsupported_claims": 4,
                "conditions_exceptions": 2,
                "relevance": 4,
                "source_consistency": 4,
            }
        elif only_sg and processing and cutoff:
            # Step3 OFF-like: processing+cutoff but missing method table (#2).
            scores = {
                "correctness": 3,
                "completeness": 2,
                "evidence_utilization": 3,
                "unsupported_claims": 4,
                "conditions_exceptions": 3,
                "relevance": 3,
                "source_consistency": 3,
            }
        elif only_sg:
            scores = {
                "correctness": 3,
                "completeness": 1,
                "evidence_utilization": 1,
                "unsupported_claims": 4,
                "conditions_exceptions": 2,
                "relevance": 3,
                "source_consistency": 3,
            }
        else:
            scores = {
                "correctness": 2,
                "completeness": 1,
                "evidence_utilization": 1,
                "unsupported_claims": 3,
                "conditions_exceptions": 2,
                "relevance": 2,
                "source_consistency": 2,
            }
        if fab:
            scores["unsupported_claims"] = min(scores["unsupported_claims"], 2)
        note = (
            f"methods={methods} only_sg={only_sg} processing={processing} "
            f"cutoff={cutoff}; primary_missing={sorted(missing)}"
        )

    elif query_id == "Q2":
        step_verify = _any(a, "verify") and _any(a, "tracking", "carrier")
        step_contact = _any(a, "contact") and _any(a, "carrier")
        step_offer = _any(a, "replacement") or (
            _any(a, "refund") and _any(a, "offer")
        )
        steps = sum([step_verify, step_contact, step_offer])
        seven = _any(a, "7 calendar")
        collapsed = steps <= 1 and len(a) < 280
        completeness = 4 if steps == 3 else (3 if steps == 2 else (2 if steps == 1 else 1))
        if collapsed:
            completeness = min(completeness, 1)
            util = 1
        else:
            util = 4 if steps == 3 else (3 if steps == 2 else 2)
        correctness = 4 if steps >= 2 and seven else (3 if steps >= 1 else 2)
        conditions = 4 if seven and step_offer else (3 if seven else 2)
        scores = {
            "correctness": correctness,
            "completeness": completeness,
            "evidence_utilization": util,
            "unsupported_claims": 4,
            "conditions_exceptions": conditions,
            "relevance": 4,
            "source_consistency": 4 if steps >= 2 else 3,
        }
        note = f"steps={steps} seven={seven} collapsed={collapsed}"

    elif query_id == "Q3":
        overdue_def = _any(a, "promised delivery") or _any(
            a, "delivery date has passed"
        )
        seven_rule = _any(a, "7 calendar")
        auto_refund_wrong = _any(
            a, "automatically granted", "automatic refund", "always get a refund"
        )
        has_five = "delivery_policy.md#5" in in_ctx or "delivery_policy.md#5" in neighbor_labels
        completeness = 4 if overdue_def and seven_rule else (
            2 if overdue_def or seven_rule else 1
        )
        util = 4 if seven_rule and has_five else (
            3 if seven_rule else (2 if overdue_def else 1)
        )
        correctness = 2 if auto_refund_wrong else (
            4 if overdue_def and seven_rule else (3 if overdue_def else 2)
        )
        conditions = 4 if seven_rule and not auto_refund_wrong else (
            2 if not seven_rule else 3
        )
        unsupported = 2 if auto_refund_wrong else 4
        scores = {
            "correctness": correctness,
            "completeness": completeness,
            "evidence_utilization": util,
            "unsupported_claims": unsupported,
            "conditions_exceptions": conditions,
            "relevance": 4 if overdue_def or seven_rule else 3,
            "source_consistency": 4 if seven_rule or overdue_def else 3,
        }
        note = (
            f"overdue_def={overdue_def} seven_rule={seven_rule} "
            f"auto_refund_wrong={auto_refund_wrong} has_#5={has_five}"
        )

    elif query_id == "Q4":
        pto = _any(a, "pto") or _any(a, "paid time")
        manager = _any(a, "manager", "approve", "request")
        completeness = 4 if pto and manager else 3
        scores = {
            "correctness": 4 if pto else 3,
            "completeness": completeness,
            "evidence_utilization": 4 if pto else 3,
            "unsupported_claims": 4,
            "conditions_exceptions": 3 if _any(a, "business day", "advance", "notice") else 3,
            "relevance": 4,
            "source_consistency": 4,
        }
        note = f"pto={pto} manager={manager}"

    elif query_id == "Q5":
        listed_cats = sum(
            [
                _any(a, "refund_request"),
                _any(a, "shipping", "delivery"),
                _any(a, "product_defect", "product defect"),
                _any(a, "account"),
                _any(a, "general_inquiry", "bill"),
            ]
        )
        ticket = _any(a, "ticket", "support")
        invented_ui = _any(
            a, "website form", "click here", "navigate to the contact"
        )
        has_cat_chunk = (
            "customer_support_guidelines.md#1" in in_ctx
            or "customer_support_guidelines.md#1" in neighbor_labels
        )
        if listed_cats >= 4:
            scores = {
                "correctness": 4,
                "completeness": 4,
                "evidence_utilization": 4,
                "unsupported_claims": 4,
                "conditions_exceptions": 3,
                "relevance": 4,
                "source_consistency": 4,
            }
        elif listed_cats >= 2:
            scores = {
                "correctness": 3,
                "completeness": 3,
                "evidence_utilization": 3 if has_cat_chunk else 2,
                "unsupported_claims": 4,
                "conditions_exceptions": 3,
                "relevance": 4,
                "source_consistency": 4,
            }
        elif ticket:
            # Mentions ticket fields but no category list (OFF-like).
            scores = {
                "correctness": 2,
                "completeness": 2,
                "evidence_utilization": 2,
                "unsupported_claims": 4,
                "conditions_exceptions": 2,
                "relevance": 3,
                "source_consistency": 3,
            }
        else:
            scores = {
                "correctness": 2,
                "completeness": 1,
                "evidence_utilization": 1,
                "unsupported_claims": 3,
                "conditions_exceptions": 2,
                "relevance": 2,
                "source_consistency": 2,
            }
        if invented_ui:
            scores["unsupported_claims"] = 1
            scores["source_consistency"] = min(scores["source_consistency"], 3)
        note = (
            f"listed_cats≈{listed_cats} invented_ui={invented_ui} "
            f"has_cat_chunk={has_cat_chunk}"
        )

    elif query_id == "Q6":
        photo = _any(a, "photographic", "photo evidence", "photos")
        soft_miss = (not photo) and _any(
            a,
            "no specific evidence",
            "without defect",
            "no restocking fee",
        )
        denied = (not photo) and _any(
            a, "not required", "no evidence", "does not require", "don't need"
        )
        # Severe regression: denies or fails to surface photo evidence in context.
        if denied or soft_miss:
            scores = {
                "correctness": 1,
                "completeness": 1,
                "evidence_utilization": 1,
                "unsupported_claims": 2,
                "conditions_exceptions": 1,
                "relevance": 2,
                "source_consistency": 2,
            }
            note = "REGRESSION: denies/misses photographic evidence"
        else:
            ticket = _any(a, "support ticket", "ticket")
            completeness = 4 if photo and ticket else (3 if photo else 2)
            scores = {
                "correctness": 4 if photo else 2,
                "completeness": completeness,
                "evidence_utilization": 4 if photo else 2,
                "unsupported_claims": 4,
                "conditions_exceptions": 4 if photo else 2,
                "relevance": 4,
                "source_consistency": 4 if photo else 3,
            }
            note = f"photo={photo} ticket={ticket}"

    elif query_id == "Q7":
        vpn = _any(a, "vpn")
        patch = _any(a, "patch", "os ")
        completeness = 4 if vpn and patch else (3 if vpn or patch else 2)
        scores = {
            "correctness": 4 if vpn else 3,
            "completeness": completeness,
            "evidence_utilization": 4 if vpn else 3,
            "unsupported_claims": 4,
            "conditions_exceptions": 3,
            "relevance": 4,
            "source_consistency": 4,
        }
        note = f"vpn={vpn} patch={patch}"

    else:
        scores = {m: 2 for m in METRICS}
        note = "unknown query"

    total = sum(scores[m] for m in METRICS)
    return {
        "scores": scores,
        "total": total,
        "note": note,
    }


def score_results_file(results: dict[str, Any]) -> dict[str, Any]:
    """Score every seed run in a hybrid stability results JSON."""
    out: dict[str, Any] = {
        "meta": {
            "method": (
                "Checklist-assisted scoring aligned with Step 3 rubric; "
                "not LLM-as-judge"
            ),
            "seeds": results.get("meta", {}).get("seeds"),
            "configs": results.get("meta", {}).get("configs"),
            "rubric": "seven metrics 0-4; unsupported_claims higher=fewer",
        },
        "per_run": {},
        "aggregates": {},
    }

    for qid, qentry in results.get("questions", {}).items():
        out["per_run"][qid] = {}
        for conf, cfg in qentry.get("configs", {}).items():
            neighbors = [n["label"] for n in cfg.get("neighbors", [])]
            conf_runs = []
            for run in cfg.get("runs", []):
                scored = score_answer(
                    qid,
                    run.get("answer", ""),
                    primary_in_context=cfg.get("primary_in_context", []),
                    primary_missing=cfg.get("primary_missing_from_context", []),
                    neighbor_labels=neighbors,
                )
                conf_runs.append(
                    {
                        "seed": run.get("seed"),
                        "total": scored["total"],
                        "scores": scored["scores"],
                        "note": scored["note"],
                        "answer_preview": (run.get("answer") or "")[:240],
                    }
                )
            totals = [r["total"] for r in conf_runs]
            out["per_run"][qid][conf] = {
                "runs": conf_runs,
                "mean_total": sum(totals) / len(totals) if totals else 0,
                "min_total": min(totals) if totals else 0,
                "max_total": max(totals) if totals else 0,
                "neighbor_count": cfg.get("neighbor_count"),
                "context_char_len": cfg.get("context_char_len"),
                "irrelevant_neighbor_count": cfg.get(
                    "irrelevant_neighbor_count"
                ),
                "cap_respected": cfg.get("cap_respected"),
                "answers_identical_across_seeds": cfg.get(
                    "answers_identical_across_seeds"
                ),
            }

    # Config-level aggregates across questions
    configs = results.get("meta", {}).get("configs") or []
    for conf in configs:
        all_totals: list[float] = []
        per_q_means: dict[str, float] = {}
        ctxs: list[int] = []
        nbrs: list[int] = []
        irrs: list[int] = []
        for qid in out["per_run"]:
            cell = out["per_run"][qid].get(conf)
            if not cell:
                continue
            per_q_means[qid] = cell["mean_total"]
            all_totals.extend(r["total"] for r in cell["runs"])
            ctxs.append(cell["context_char_len"] or 0)
            nbrs.append(cell["neighbor_count"] or 0)
            irrs.append(cell["irrelevant_neighbor_count"] or 0)
        n = len(all_totals)
        mean = sum(all_totals) / n if n else 0
        sorted_t = sorted(all_totals)
        median = (
            sorted_t[n // 2]
            if n % 2 == 1
            else (sorted_t[n // 2 - 1] + sorted_t[n // 2]) / 2
            if n
            else 0
        )
        var = (
            sum((x - mean) ** 2 for x in all_totals) / n if n else 0
        )
        std = var ** 0.5
        out["aggregates"][conf] = {
            "mean_total": round(mean, 3),
            "median_total": median,
            "std_total": round(std, 3),
            "min_total": min(all_totals) if all_totals else 0,
            "max_total": max(all_totals) if all_totals else 0,
            "n_scores": n,
            "per_question_mean": per_q_means,
            "mean_context_chars": round(sum(ctxs) / len(ctxs), 1) if ctxs else 0,
            "max_context_chars": max(ctxs) if ctxs else 0,
            "mean_neighbors": round(sum(nbrs) / len(nbrs), 2) if nbrs else 0,
            "mean_irrelevant_neighbors": (
                round(sum(irrs) / len(irrs), 2) if irrs else 0
            ),
        }
    return out


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    path = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "experiments/retrieval_eval/hybrid_expansion_stability_results.json"
    )
    results = json.loads(path.read_text(encoding="utf-8"))
    scored = score_results_file(results)
    out = path.with_name("hybrid_expansion_stability_scores.json")
    out.write_text(json.dumps(scored, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    for conf, agg in scored["aggregates"].items():
        print(
            f"{conf}: mean={agg['mean_total']} std={agg['std_total']} "
            f"ctx={agg['mean_context_chars']} nbr={agg['mean_neighbors']}"
        )
