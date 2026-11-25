# Step 8 — Guarded HYBRID_CAP2 Experiment Report

**Verdict:** **PROMISING — REQUIRES FURTHER VALIDATION**  
**Mode:** Isolated experiment only (production untouched)  
**Results:** `experiments/retrieval_eval/step8_guarded_hybrid/guarded_hybrid_results.json`  
**Seeds:** `101, 202, 303, 404, 505` (matched across all configs)

---

## 1. Experiment Objective

Test whether a **deterministic evidence-sufficiency guard** improves reliability of HYBRID_CAP2 neighbor expansion by:

1. Inspecting original semantic hits.
2. Skipping expansion when retrieved text already appears sufficient for the question’s information need.
3. Applying unchanged HYBRID_CAP2 only when evidence looks incomplete.

Focus problem from Steps 6–7: Q6 distraction via `refund_policy.md#5` (restocking fee) despite photographic evidence already in retrieved `refund_policy.md#1`.

**Constraint:** Guard must be general (no hardcoded Q6 / document rules) and must not use evaluation ground truth at runtime.

---

## 2. Architecture and Guard Design

### 2.1 Inspected baseline (findings)

| Asset | Role in Step 8 |
|---|---|
| `selective_strategies.plan_hybrid` | Unchanged HYBRID_CAP2 planner (C∪A, priority, cap) |
| `run_hybrid_stability_experiment.py` | Pattern for seed×config harness (not overwritten) |
| `hybrid_scoring.py` | Same Step 3 checklist-assisted rubric |
| `dataset.py` Q1–Q7 | Unchanged questions / ground truth |
| Production `neighbor_expansion.py` / `rag.py` | **Not modified**; context formatting reused read-only |

HYBRID_CAP2 in prior work = `plan_hybrid(..., max_expanded=8)` then relevance filter then hard cap **2**.

### 2.2 New components

```
hits = semantic_search(question)
guard = assess_evidence_sufficiency(question, hits)   # runtime only
if guard.skip_expansion:
    context = retrieved_only
else:
    neighbors = plan_hybrid(...)  # unchanged
    context = retrieved + neighbors
answer = ollama(chat, seed=S, temperature=0.2)
```

Offline GT is used **only** after the run for FP/FN analysis.

---

## 3. Evidence Sufficiency Criteria

Deterministic pipeline in `evidence_guard.py`:

1. **Classify need** from question wording only:  
   `requirement_evidence` | `procedure` | `duration_table` | `eligibility` | `contact_support` | `general`
2. **Apply need-specific checks** on retrieved chunk texts:
   - **Requirement/evidence:** topical overlap + requirement cues (`require*` / `must` / `supported by`, …) in a retrieved chunk.
   - **Procedure:** ≥3 numbered steps / complete “Support agents must” list; incomplete procedure signals → expand.
   - **Duration/table:** incomplete/truncated tables → expand; complete multi-method duration table → skip.
   - **Eligibility:** overdue definition without lost-package calendar-day rule when question implies late/refund → expand.
   - **Contact/support:** requires a **single-chunk** category listing/table (not scattered tokens across docs).
   - **General:** conservative — skip only with strong lexical coverage and no incompleteness signals.
3. **Default:** `INSUFFICIENT` → allow expansion when unsure.
4. **Empty retrieval:** safe no-op (no neighbors).

**Explicitly avoided:** question IDs, GT chunk labels, similarity-only sufficiency, LLM judge.

---

## 4. Files Created and Modified

| Path | Action |
|---|---|
| `experiments/retrieval_eval/evidence_guard.py` | **Created** — guard + `plan_guarded_hybrid_cap2` |
| `experiments/retrieval_eval/test_evidence_guard.py` | **Created** — unit tests |
| `experiments/retrieval_eval/run_guarded_hybrid_experiment.py` | **Created** — 4-config × 5-seed runner |
| `experiments/retrieval_eval/step8_guarded_hybrid/guarded_hybrid_results.json` | **Created** — machine-readable results |
| `experiments/retrieval_eval/GUARDED_HYBRID_CAP2_EXPERIMENT_REPORT.md` | **Created** — this report |
| `experiments/retrieval_eval/selective_strategies.py` | **Unchanged** this step (HYBRID_CAP2 intact) |
| `backend/**` | **Unchanged** |

Prior Step 3–7 reports/baselines were **not** overwritten.

---

## 5. Test Results

```
pytest experiments/retrieval_eval/test_evidence_guard.py tests/test_retrieval_eval_metrics.py
32 passed
```

Guard tests covered: sufficient→skip, incomplete→expand, empty retrieval, multi-chunk handling, determinism, no GT tokens in guard source, HYBRID/OFF/BLIND planners still callable/unchanged.

---

## 6. Experiment Methodology

| Setting | Value |
|---|---|
| Configs | OFF, BLIND, HYBRID_CAP2, GUARDED_HYBRID_CAP2 |
| Questions | Q1–Q7 (unchanged) |
| Seeds | 101, 202, 303, 404, 505 |
| Model | `llama3.2` via Ollama `/api/chat` + `options.seed` |
| Temperature | `0.2` |
| Retrieval | `top_k=5`, `min_similarity=0.5` (once per question) |
| Prompt | Production `rag_system_prompt` |
| Order | question → config → seeds |
| Scoring | Same Step 3 seven-metric checklist (`hybrid_scoring.py`) |
| Generations | 4 × 7 × 5 = **140** |

Verified: `semantic_hits_identical_across_configs == true` for all questions.

---

## 7. Configuration Comparison

| Config | Mean (/28) | Median | Std (sample) | Mean ctx chars | Mean neighbors |
|---|---:|---:|---:|---:|---:|
| OFF | 22.657 | 23 | 3.933 | 4405 | 0.00 |
| BLIND | 22.886 | 23 | 3.496 | 7687 | 6.29 |
| HYBRID_CAP2 | 22.343 | 23 | 5.070 | 5183 | 1.43 |
| **GUARDED_HYBRID_CAP2** | **24.114** | **25** | **3.554** | **4830** | **0.71** |

Guarded hybrid is best on mean/median among the four arms, with ~37% fewer mean context characters than BLIND and lower neighbor noise than unguarded HYBRID.

---

## 8. Per-Question Mean Totals

| Q | OFF | BLIND | HYBRID_CAP2 | GUARDED |
|---|---:|---:|---:|---:|
| Q1 | 19.4 | 21.8 | **24.8** | **24.8** |
| Q2 | 23.2 | 19.6 | 21.6 | **23.2** |
| Q3 | 19.2 | 20.2 | **22.2** | **22.2** |
| Q4 | 26.0 | 26.0 | 26.0 | 26.0 |
| Q5 | 19.8 | 21.6 | 21.6 | 21.6 |
| Q6 | **28.0** | **28.0** | **17.2** | **28.0** |
| Q7 | 23.0 | 23.0 | 23.0 | 23.0 |

Guarded preserves HYBRID’s Q1/Q3 gains, restores Q2 to OFF-level (by skipping unnecessary expansion), and **fully repairs Q6**.

---

## 9. Statistical Analysis (paired, matched question×seed)

n=35 cells per contrast (7×5). Bootstrap 95% CI for mean diff (descriptive; cells within a question share context).

| Contrast | Mean Δ | Boot 95% CI | + / − / 0 |
|---|---:|---|---|
| GUARDED − OFF | **+1.46** | **[+0.29, +2.69]** | 10 / 2 / 23 |
| GUARDED − BLIND | **+1.23** | **[0.00, +2.51]** | 10 / 3 / 22 |
| GUARDED − HYBRID_CAP2 | **+1.77** | **[+0.06, +3.77]** | 5 / 1 / 29 |
| HYBRID_CAP2 − OFF | −0.31 | [−2.69, +1.97] | 11 / 7 / 17 |
| BLIND − OFF | +0.23 | [−1.09, +1.49] | 7 / 4 / 24 |

**Interpretation:** On this small battery, guarded hybrid’s mean advantage over OFF and unguarded HYBRID has CIs excluding 0. vs BLIND the lower bound touches 0. This is **encouraging but not confirmatory** (n_questions=7, checklist scoring, same corpus).

---

## 10. Q6 Investigation

| Config | Neighbors | Seed totals (101…505) |
|---|---|---|
| OFF | ∅ | 28,28,28,28,28 |
| BLIND | 8 incl. `#5` | 28,28,28,28,28 |
| HYBRID_CAP2 | `#3`, `#5` | 28, **10**, **10**, 28, **10** |
| **GUARDED** | **∅ (skipped)** | **28,28,28,28,28** |

**Confirmed:**

- Guard classified need=`requirement_evidence` and found a requirement statement in retrieved `refund_policy.md#1` → skip.
- Restocking-fee neighbor `#5` was **not** introduced under GUARDED.
- Unguarded HYBRID still failed 3/5 seeds with the same distraction pattern.
- Answer quality for GUARDED Q6 was stable across all five seeds.

This is a **general requirement-sufficiency rule**, not a Q6 hardcoded branch (verified by unit test scanning guard source for `Q6` / GT symbols).

---

## 11. Guard False-Positive / False-Negative Analysis

Offline oracle: “sufficient” iff **all** `primary_relevant` labels appear in semantic hits (analysis only).

| | Count | Questions |
|---|---:|---|
| Skip | 3 | Q2, Q6, Q7 |
| Expand | 4 | Q1, Q3, Q4, Q5 |
| True positive skip | 3 | Q2, Q6, Q7 |
| False positive skip | **0** | — |
| True negative expand | 3 | Q1, Q3, Q5 |
| False negative expand | 1 | Q4 |

Q4 FN: guard expanded, but HYBRID planned **0** neighbors anyway → behavior matched skip in practice.

**No FP skips** on this set after tightening contact-support criteria (scattered category tokens no longer count).

---

## 12. Context Size Comparison

| Config | Mean chars | Max chars | Mean neighbors | Mean irrelevant neighbors |
|---|---:|---:|---:|---:|
| OFF | 4405 | 4482 | 0.00 | 0.00 |
| BLIND | 7687 | 9457 | 6.29 | 5.86 |
| HYBRID_CAP2 | 5183 | 5708 | 1.43 | 1.00 |
| GUARDED | **4830** | 5708 | **0.71** | **0.29** |

Guarded keeps selective expansion where needed (Q1/Q3/Q5) and drops it where original hits already answer (Q2/Q6/Q7).

---

## 13. Limitations

1. Still only **7 questions**; gains may not generalize.
2. Checklist scoring is labeled / hypothesis-informed (not blind dual annotation).
3. Need classifier is heuristic; new question phrasings may mis-route.
4. “Requirement statement present” ≠ guaranteed model utilization (though Q6 worked here).
5. Q4 shows conservative over-expansion tendency on `general` need.
6. Small-n bootstrap CIs are exploratory.
7. Does not prove production readiness or fix generation underuse on every item (Q5 still middling).

**Does the guard only “game” this dataset?**  
It was motivated by Q6 but implemented as need-typed sufficiency over retrieved text. On this run it also skipped Q2/Q7 appropriately and still expanded Q1/Q3/Q5. That is broader than a Q6 patch, yet **still needs a larger held-out question set** before claiming generality.

---

## 14. Final Verdict

### **PROMISING — REQUIRES FURTHER VALIDATION**

| Claim | Support |
|---|---|
| Guard solves the identified Q6 distraction | **Yes** on this 5-seed run (28/28, no `#5`) |
| Improves mean quality vs OFF / unguarded HYBRID | **Yes** (descriptive CIs exclude 0) |
| Beats BLIND on mean with less context | **Suggestive** (CI touches 0) |
| Ready for production deployment | **No** |

**Recommended next validation (not started):** held-out questions (abstention, exceptions, distractor neighbors), optional blind human audit of disputed cells, and a freeze of guard rules as a versioned experiment spec—still experiment-only until approved.

---

## Unchanged Confirmation

Production code, prompts, configuration defaults, semantic search, production neighbor expansion, chunking, database records, embeddings, Q1–Q7 ground truth, and prior experiment reports/baselines were **not** modified.

**Stop.** Awaiting review before any further phase.
