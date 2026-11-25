# Step 11 — GENERAL Truncation Rule Ablation Report

**Experiment mode:** Isolated evaluation only (no production changes)  
**Code root:** `experiments/retrieval_eval/step11_general_no_truncation/`  
**Raw results:** `experiments/retrieval_eval/step11_general_no_truncation/results/step11_results.json`  
**Frozen guard SHA-256 (unchanged):** `4ab51eb2ad25a7ece5062878ae713c4537df54368ee9324139b891fbaf11eae6`

---

## 1. Executive Summary

On a new independent H2 split (Q28–Q47), removing **only** the GENERAL `_chunk_truncated` expansion trigger produced **zero skip-decision divergences** versus the frozen guard (2/20 skips each; same questions). Answer scores for `GENERAL_NO_TRUNCATION` and `HYBRID_CAP2` were **identical** (mean **28.0 / 28**, paired difference **0.0**, 95% bootstrap CI `[0.0, 0.0]`).

**Why:** On every H2 question where top-5 hits included truncation, at least one hit also fired `_table_appears_incomplete` or `_procedure_needs_next`. Truncation therefore did not uniquely determine GENERAL expansion on this corpus/windowing regime.

| Verdict question | Answer |
|---|---|
| Does GENERAL truncation cause unnecessary expansion? | **Not as a sole cause on H2** — it co-occurs with other GENERAL incompleteness signals |
| Does removing it improve answer quality? | **No** vs HYBRID_CAP2; tiny/uncertain edge vs OFF; clear edge vs BLIND (Q46) |
| Harm neighbor-needed questions? | **No observed harm** on annotated neighbor-helpful items |
| Hold across questions/seeds? | **Yes for the null ablation effect** (0/20 divergences; ceiling scores) |
| Better than OFF / BLIND / HYBRID? | **Ties HYBRID**; better than BLIND; ≈OFF with less OFF seed variance on Q38 |
| Justify another independent validation of *this* ablation? | **Low priority** — next work should target co-occurring GENERAL signals or truncation-only strata |

**Do not ship. Do not claim production readiness.**

---

## 2. Research Question

Does removing the GENERAL truncation-based expansion trigger improve answer quality and reduce unnecessary context without harming answer completeness?

---

## 3. Step 10 Findings Recap

From `GUARD_GENERALIZATION_FAILURE_ANALYSIS_REPORT.md` (read-only; not modified):

1. **Weak classification coverage** — held-out H1 (Q8–Q27): 19/20 classified `general`.
2. **Over-conservative GENERAL sufficiency** — GENERAL expands if *any* top-5 hit shows incompleteness, including `_chunk_truncated`, incomplete tables, or procedure-needs-next.
3. Step 9: GUARDED_HYBRID_CAP2 **did not generalize** (tied HYBRID; 0 skips).
4. Blind expansion can help some neighbor-gap cases (e.g. Q19) but is not generally superior.

Step 11 isolates finding (2)’s truncation component only.

---

## 4. Dataset Design

**Split:** H2 = Q28–Q47 (20 questions).  
**Not used:** Q1–Q7 (dev), Q8–Q27 (H1 / Step 9).

| Coverage intent | H2 items |
|---|---|
| Procedure | Q46, Q47 |
| Requirement evidence | Q45 |
| General policy / numerical / list / contact | Q28–Q44 (majority) |
| Duration-style wording | Q33, Q34 |
| Original evidence usually sufficient | 18 annotated `expects_neighbor_helpful=False` |
| Neighbor may help | Q41, Q47 |
| Chunk-boundary / truncation regime | Nearly all (500-char windows) |
| Distracting neighbors possible | Observed under BLIND (esp. Q46) |

Details: `step11_general_no_truncation/DATASET.md`.

---

## 5. Dataset Independence and Ground Truth Validation

| Check | Result |
|---|---|
| ID disjoint from Q1–Q27 | Pass |
| Primary chunk facts present in cited chunk text | Pass (offline string probe for all answer-key facts/groups) |
| Answer key used only in scoring | Pass (`h2_answer_key.py` not imported by guard) |
| No question-ID hardcoding in ablation logic | Pass |
| Ablation logic tuned on H2 scores | No — ablation defined before live scoring |

Corpus is the same NovaForge policy set used in prior steps; **questions and labels are new**. Historical mean scores from H1/dev are **not directly comparable** without accounting for different items and ceiling effects on H2.

---

## 6. Experimental Configurations

| Config | Behavior |
|---|---|
| OFF | No neighbor expansion |
| BLIND | ±1 neighbors (uncapped hybrid filter not applied; max_expanded=10) |
| HYBRID_CAP2 | Unchanged selective hybrid, cap 2 after relevance filter |
| GENERAL_NO_TRUNCATION | Ablated GENERAL sufficiency → then same HYBRID_CAP2 planner if expand |

**Ablation invariant:** specialized need classifiers and checkers unchanged; only GENERAL drops `_chunk_truncated` from the incompleteness OR. Semantic ranking unchanged.

Frozen-guard decisions logged diagnostically (not a scored fifth config).

---

## 7. Implementation Details

| File | Role |
|---|---|
| `general_no_truncation_guard.py` | Ablated assess + `plan_general_no_truncation` |
| `h2_dataset.py` / `h2_answer_key.py` / `h2_scoring.py` | H2 data + offline rubric (max 28) |
| `run_step11_eval.py` | Matched seeds harness |
| `test_step11.py` | Unit isolation tests (7 passed) |
| `REPRODUCIBILITY.md` | Run commands |

Production RAG, prompts, DB, embeddings, `evidence_guard.py`, and Steps 8–10 artifacts were not modified.

---

## 8. Environment and Reproducibility

| Item | Value |
|---|---|
| Timestamp (UTC) | 2026-11-24T09:49:30 → 10:05:12 |
| Python | 3.14.7 |
| Platform | macOS-27.0.1-arm64 |
| LLM | `llama3.2` via Ollama |
| Embeddings | `nomic-embed-text` |
| top_k / min_sim / temp | 5 / 0.5 / 0.2 |
| Seeds | 101, 202, 303, 404, 505 |
| Order | question → config → seeds |
| Cells | 20 × 4 × 5 = **400** scored answers |

```bash
PYTHONPATH=backend:. python -m experiments.retrieval_eval.step11_general_no_truncation.run_step11_eval
```

---

## 9. Aggregate Results

| Config | Mean total | Sample std | Mean context chars | Mean neighbors | Mean completeness | Mean correctness | Mean unsupported |
|---|---:|---:|---:|---:|---:|---:|---:|
| OFF | 27.920 | 0.800 | 4378.3 | 0.00 | 3.98 | 3.99 | 3.99 |
| BLIND | 27.400 | 2.629 | 7172.8 | 5.40 | 3.90 | 3.90 | 3.95 |
| HYBRID_CAP2 | **28.000** | 0.000 | 4897.3 | 1.05 | 4.00 | 4.00 | 4.00 |
| GENERAL_NO_TRUNCATION | **28.000** | 0.000 | 4824.4 | 0.90 | 4.00 | 4.00 | 4.00 |

**True guard skips (diagnostic):** frozen **2/20**, ablation **2/20**, divergences **0**.  
Skips were Q45 (`requirement_evidence`) and Q46 (`procedure`) — specialized paths, not GENERAL.

H2 shows a **score ceiling** for HYBRID and ablation (all seeds 28). Interpretation of quality *gains* is limited; expansion/skip behavior remains informative.

---

## 10. Per-Question Results

Per-question mean totals (5 seeds). Variance was 0 for HYBRID and GENERAL_NO_TRUNCATION on all items.

| QID | OFF | BLIND | HYBRID | GEN_NO_TRUNC | Frozen skip | Ablation skip | nbrH | nbrA | Need |
|---|---:|---:|---:|---:|---|---|---:|---:|---|
| Q28 | 28 | 28 | 28 | 28 | no | no | 2 | 2 | general |
| Q29 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q30 | 28 | 28 | 28 | 28 | no | no | 0 | 0 | general |
| Q31 | 28 | 28 | 28 | 28 | no | no | 0 | 0 | general |
| Q32 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q33 | 28 | 28 | 28 | 28 | no | no | 0 | 0 | duration_table |
| Q34 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | duration_table |
| Q35 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q36 | 28 | 28 | 28 | 28 | no | no | 2 | 2 | general |
| Q37 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q38 | 26.4 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q39 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q40 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q41 | 28 | 28 | 28 | 28 | no | no | 0 | 0 | general |
| Q42 | 28 | 28 | 28 | 28 | no | no | 2 | 2 | general |
| Q43 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | general |
| Q44 | 28 | 28 | 28 | 28 | no | no | 2 | 2 | general |
| Q45 | 28 | 28 | 28 | 28 | **yes** | **yes** | 1 | 0 | requirement_evidence |
| Q46 | 28 | **16** | 28 | 28 | **yes** | **yes** | 2 | 0 | procedure |
| Q47 | 28 | 28 | 28 | 28 | no | no | 1 | 1 | procedure |

HYBRID and GENERAL_NO_TRUNCATION contexts matched on **18/20** questions; differ only on Q45/Q46 (specialized skips).

---

## 11. Statistical Analysis

Paired differences on question×seed cells (n=100):

| Contrast | Mean diff | 95% bootstrap CI | + / − / 0 |
|---|---:|---|---|
| GENERAL_NO_TRUNCATION − OFF | +0.08 | [0.00, 0.24] | 1 / 0 / 99 |
| GENERAL_NO_TRUNCATION − BLIND | +0.60 | [0.12, 1.20] | 5 / 0 / 95 |
| GENERAL_NO_TRUNCATION − HYBRID_CAP2 | **0.00** | **[0.00, 0.00]** | 0 / 0 / 100 |
| HYBRID_CAP2 − OFF | +0.08 | [0.00, 0.24] | 1 / 0 / 99 |
| BLIND − OFF | −0.52 | [−1.12, −0.04] | 1 / 5 / 94 |
| BLIND − HYBRID_CAP2 | −0.60 | [−1.20, −0.12] | 0 / 5 / 95 |

Question-level CIs are exploratory (n=20). The ablation-vs-HYBRID null is exact under this rubric and seed set.

---

## 12. Evidence Completeness Analysis

| Slice | OFF | BLIND | HYBRID | GEN_NO_TRUNC |
|---|---:|---:|---:|---:|
| `expects_neighbor_helpful` (Q41, Q47) | 28.0 | 28.0 | 28.0 | 28.0 |
| Annotated original-sufficient (18 qs) | 27.911 | 27.333 | 28.0 | 28.0 |

Completeness / correctness / unsupported means are perfect (4.0) for HYBRID and GENERAL_NO_TRUNCATION. OFF’s only soft miss cluster is Q38 (one seed scored 20). BLIND’s completeness failure is Q46 (mean 16): distracting ±1 neighbors suppressed required facts (`7 calendar days` / contact steps).

Ablation **did not** skip any GENERAL question that OFF already answered from original hits; specialized skips (Q45/Q46) preserved perfect completeness with **less** context than HYBRID.

---

## 13. Neighbor Expansion Analysis

| Metric | Observation |
|---|---|
| Truncation-only incompleteness questions | **0 / 20** |
| Skip divergences (frozen vs ablation) | **0 / 20** |
| GENERAL questions still expanding under ablation | All GENERAL items still `insufficient` via table/procedure signals |
| Mean neighbors | HYBRID 1.05 → ablation 0.90 (−0.15 from Q45/Q46 skips only) |
| Mean context chars | 4897 → 4824 (−~73; specialized skips) |
| Blind expansion | Highest context (7172) and only severe quality drop (Q46) |

**Confirmed mechanism on H2:** GENERAL incompleteness is an OR of truncation **or** table incompleteness **or** procedure-needs-next. Removing truncation alone leaves the other two, which fire via top-5 distractors under 500-char chunking.

---

## 14. Failure Cases

1. **Q46 + BLIND (16/28 all seeds):** Overdue procedure answered correctly under OFF/HYBRID/ablation; blind neighbors dilute/distract. Supports “blind can hurt” (consistent with Step 10’s caution).
2. **Q38 + OFF (one seed 20/28):** Seed variance without expansion; HYBRID/ablation/BLIND stable at 28.
3. **No ablation-induced completeness failures** on neighbor-helpful annotations.

---

## 15. Comparison with Historical Findings

| Historical claim | H2 ablation relation |
|---|---|
| Step 9: GUARDED ≡ HYBRID on H1 (0 skips) | Compatible: GENERAL still expands when incompleteness OR fires |
| Step 10: truncation over-triggers GENERAL | **Refined:** truncation is present almost always, but **not uniquely causal** when table/procedure signals co-occur |
| Step 10: classification coverage weak | Reproduced: most H2 items still `general`; skips only on specialized needs (Q45/Q46) |
| Step 10: blind sometimes helps (Q19) | H2 shows blind **hurts** Q46; help/harm is question-dependent |

**Dataset caveat:** H2 means sit near rubric ceiling; H1 means were also high but not identical items. Do not treat Δmean across steps as a calibrated effect size.

---

## 16. Confirmed Findings

1. **CONFIRMED:** Isolating removal of GENERAL `_chunk_truncated` yields **no skip-decision change** on H2 (0 divergences).
2. **CONFIRMED:** On H2, **0 questions** had truncation as the *only* top-5 incompleteness signal.
3. **CONFIRMED:** `GENERAL_NO_TRUNCATION` answer totals **equal** `HYBRID_CAP2` on all 100 paired cells.
4. **CONFIRMED:** Specialized procedure / requirement_evidence paths still skip when sufficient (Q45, Q46).
5. **CONFIRMED:** Blind expansion can degrade completeness (Q46) while selective/hybrid/ablation do not on that item.
6. **LIKELY:** Further GENERAL conservatism is driven at least as much by **table/procedure incompleteness on any hit** (including distractors) as by truncation per se.

---

## 17. Limitations

- H2 score ceiling compresses sensitivity to quality improvements.
- Same underlying corpus as prior steps (new questions, not a new document collection).
- Only 2 annotated neighbor-helpful items; neither stressed a “must expand or fail” regime under OFF (both already 28 with OFF).
- Rubric is checklist/fact-string based (not LLM-as-judge); may miss nuance.
- `mean_neighbors=0` on some HYBRID rows reflects empty post-filter plans, not guard skips.
- Five seeds / one local Ollama model — reproducibility across hardware may vary slightly.

---

## 18. Final Verdict

1. **Does GENERAL truncation cause unnecessary expansion?**  
   **Not uniquely on H2.** Truncation is pervasive but co-occurs with table/procedure incompleteness; removing truncation alone did not stop GENERAL expansion.

2. **Does removing it improve answer quality?**  
   **No vs HYBRID_CAP2** (exact tie). Marginal/uncertain vs OFF; better than BLIND mainly via avoiding Q46 failure.

3. **Does it harm questions requiring additional neighbors?**  
   **No evidence of harm** on H2 neighbor-helpful annotations.

4. **Does the improvement hold across questions and seeds?**  
   There is **no quality improvement to hold**; the **null ablation effect** holds across all 20 questions and 5 seeds.

5. **Is GENERAL_NO_TRUNCATION better than OFF, BLIND, or HYBRID_CAP2?**  
   **Ties HYBRID_CAP2** (best tier); **better than BLIND**; **≈OFF** with slightly more stable Q38. Context slightly lower than HYBRID only from specialized skips already present in the frozen guard.

6. **Sufficiently reliable to justify another independent validation of this same ablation?**  
   **No — low value.** The isolation result is clear: truncation-only ablation is underpowered when other GENERAL signals dominate. Prefer a **new** experiment (below), not a repeat of this ablation on another random split.

**Shipping decision:** Do **not** implement or ship GENERAL_NO_TRUNCATION to production.

---

## 19. Recommended Next Experiment

**GENERAL incompleteness OR ablation / distractor-scoped sufficiency** (not another truncation-only redo):

- Compare variants that (a) ignore incompleteness on non-answering distractor hits, or (b) ablate table vs procedure vs truncation signals factorially.
- Optionally construct a **truncation-only stratum** (questions whose top-5 incompleteness is truncation alone) if the corpus/windowing can support it; if not, report that stratum as empty (as H2 did).
- Keep isolation under a new `experiments/retrieval_eval/step12_…/` directory; new independent split; no production changes.

---

*End of Step 11 report. Stopped for review — no further optimization implemented.*
