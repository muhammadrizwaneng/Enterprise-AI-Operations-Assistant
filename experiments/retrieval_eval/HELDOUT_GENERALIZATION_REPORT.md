# Step 9 — Held-Out Evaluation & Generalization Report

**Verdict:** **DOES NOT GENERALIZE**  
**Mode:** Experiment only (production + Step 8 guard frozen / unchanged)  
**Held-out results:** `experiments/retrieval_eval/step9_heldout/heldout_results.json`  
**Frozen guard SHA-256:** `4ab51eb2ad25a7ece5062878ae713c4537df54368ee9324139b891fbaf11eae6`

---

## 1. Experiment Objective

In plain terms: Step 8 looked **promising** on seven development questions (especially Q6).  
Step 9 asks a harder question: **does that benefit still appear on 20 new questions the guard was never tuned on?**

We compared OFF / BLIND / HYBRID_CAP2 / GUARDED_HYBRID_CAP2 on held-out **Q8–Q27**, with the Step 8 guard **frozen** (hash-locked). Development Q1–Q7 metrics were taken from the existing Step 8 artifact (not re-run, not overwritten).

---

## 2. Dataset Construction Methodology

1. Inspected all six policy Markdown files and 46 embedded chunks.  
2. Designed 20 questions covering numerical facts, procedures, multi-chunk tables, neighbor-boundary completions, and distraction risk — **not** paraphrases of Q1–Q7.  
3. Annotated primary chunk IDs + expected answer facts **offline only**.  
4. Validated that expected facts appear in annotated chunks.  
5. Spot-checked semantic retrieval (`top_k=5`, `min_similarity=0.5`).  
6. Replaced one initially chosen privacy “sell data” probe (chunk rarely retrieved) with an answerable retention question (Q23).

**Development set:** Q1–Q7 (`dataset.py`) — unchanged.  
**Held-out set:** Q8–Q27 (`heldout_dataset.py`).

---

## 3. All 20 Held-Out Questions

| ID | Question | Category | Difficulty |
|---|---|---|---|
| Q8 | What is the free shipping merchandise threshold? | multi_chunk_numerical | medium |
| Q9 | How much is standard flat shipping for below-threshold orders? | single_chunk_numerical | easy |
| Q10 | When do deliveries require adult signature confirmation? | single_chunk_policy_condition | easy |
| Q11 | How soon must customers report visible damage in transit? | single_chunk_numerical | easy |
| Q12 | What is the refund request window for standard physical products? | single_chunk_numerical | easy |
| Q13 | What is the refund window for software licenses and digital products? | single_chunk_condition | medium |
| Q14 | What restocking fee percentage may apply to opened unused returns? | single_chunk_numerical | easy |
| Q15 | Which items are listed as non-refundable? | multi_chunk_list | hard |
| Q16 | When must urgent refund disputes be escalated to an Operations Manager? | single_chunk_threshold | medium |
| Q17 | What is the first-response SLA for a medium-priority support ticket? | multi_chunk_table | medium |
| Q18 | What is the support escalation path from agent to admin? | procedural_neighbor | medium |
| Q19 | What ticket status values are used in the support workflow? | multi_chunk_procedure | hard |
| Q20 | What are NovaForge collaboration hours for employees? | single_chunk_numerical | easy |
| Q21 | How quickly must employees report suspected data leaks to IT Security? | single_chunk_numerical | easy |
| Q22 | How soon must OS patches be applied on company laptops used with VPN? | neighbor_completion | hard |
| Q23 | What retention period applies to orders and invoices? | single_chunk_numerical | easy |
| Q24 | How long are support tickets retained after closure? | multi_chunk_table | medium |
| Q25 | What email should be used for privacy questions? | neighbor_completion | medium |
| Q26 | At what stock quantity does Procurement receive an automatic reorder alert? | single_chunk_numerical | easy |
| Q27 | What is the standard warranty period for laptops? | multi_chunk_table | medium |

---

## 4. Evidence Annotations

Offline annotations live in `heldout_annotations.py` / `heldout_dataset.py` (primary chunk IDs, category, difficulty).  
Answer facts live in `heldout_answer_key.py` (used **only** by `heldout_scoring.py`).

Examples:

- Q8 primary: `delivery_policy.md#2`, `#3` (threshold spans chunk boundary).  
- Q19 primary: `customer_support_guidelines.md#3`, `#4` (status list split).  
- Q22 primary: `employee_handbook.md#5`, `#6` (VPN/patch sentence straddles boundary).

---

## 5. Data-Leakage Prevention

| Barrier | Status |
|---|---|
| Guard imports answer key / GT labels | **Blocked** (source scan + unit test) |
| Runner calls `assess_evidence_sufficiency(question, hits)` only | **Confirmed** |
| Scoring imports answer key offline | **Confirmed** (separate module) |
| Held-out IDs / facts absent from `evidence_guard.py` | **Confirmed** |
| No guard tuning on Q8–Q27 | **Confirmed** (file hash frozen) |

---

## 6. Frozen Implementation Identifier

```
experiments/retrieval_eval/evidence_guard.py
SHA-256: 4ab51eb2ad25a7ece5062878ae713c4537df54368ee9324139b891fbaf11eae6
```

Runner refuses to start if the on-disk hash differs. Step 8 results under `step8_guarded_hybrid/` were not overwritten.

---

## 7. Experiment Configurations

1. OFF  
2. BLIND  
3. HYBRID_CAP2  
4. GUARDED_HYBRID_CAP2  

Same production prompt, `llama3.2`, temperature `0.2`, `top_k=5`, `min_similarity=0.5`.

---

## 8. Five Matched Seeds

`101, 202, 303, 404, 505` — identical across all configs and questions.  
Execution order: question → config → seeds.  
Live generations: **4 × 20 × 5 = 400**.

---

## 9. Test Results

```
pytest experiments/retrieval_eval/test_heldout_dataset.py \
       experiments/retrieval_eval/test_evidence_guard.py \
       tests/test_retrieval_eval_metrics.py
44 passed
```

---

## 10. Overall Results (Held-Out Q8–Q27)

| Config | Mean (/28) | Median | Std | Mean ctx | Mean neighbors |
|---|---:|---:|---:|---:|---:|
| OFF | 27.27 | 28 | 2.73 | 4359 | 0.00 |
| **BLIND** | **27.84** | 28 | **1.13** | 6812 | 4.85 |
| HYBRID_CAP2 | 27.35 | 28 | 2.63 | 4916 | 1.00 |
| GUARDED | 27.35 | 28 | 2.63 | 4916 | 1.00 |

**Key observation:** GUARDED and HYBRID_CAP2 are **identical** on this battery (same means, same neighbors). The guard **never skipped** expansion (0/20 skips).

In plain English: on these new questions, “guarded hybrid” behaved exactly like ordinary hybrid. The special Step 8 skip logic did not fire.

---

## 11. Per-Question Results (mean /28)

Most questions scored 28 across configs (short factual answers → **ceiling effect**).

Notable exceptions:

| Q | OFF | BLIND | HYBRID | GUARDED | Note |
|---|---:|---:|---:|---:|---|
| Q13 | 26.4 | 24.8 | **28.0** | **28.0** | Hybrid/guard helped activation condition |
| Q18 | 27.0 | **28.0** | 27.0 | 27.0 | Blind slightly better |
| **Q19** | **16.0** | **28.0** | **16.0** | **16.0** | Hard multi-chunk statuses; only Blind recovered |

---

## 12. Development vs Held-Out Comparison

| Battery | OFF | BLIND | HYBRID | GUARDED | Guard skips |
|---|---:|---:|---:|---:|---:|
| Dev Q1–Q7 (Step 8) | 22.66 | 22.89 | 22.34 | **24.11** | 3/7 |
| Held-out Q8–Q27 | 27.27 | **27.84** | 27.35 | 27.35 | **0/20** |

**Interpretation (simple English):**  
On the small development set, the guard looked helpful mainly because it sometimes said “we already have enough evidence—don’t add noisy neighbors” (Q6).  
On the held-out set, it almost always said “not sure—expand anyway,” so it could not reproduce that advantage. Held-out scores are also near the ceiling, so differences shrink.

---

## 13. Statistical Analysis

**Cell unit:** matched `(question, seed)` — n=100 for held-out (20×5).  
**Question unit:** n=20 question-means (preferred for interpretation; still small).

| Contrast | Cell mean Δ | Boot 95% CI | Question mean Δ | Q-level boot 95% CI |
|---|---:|---|---:|---|
| GUARDED − OFF | +0.08 | [0.00, +0.24] | +0.08 | [0.00, +0.24] |
| GUARDED − BLIND | −0.49 | [−1.08, +0.04] | −0.49 | [−1.85, +0.38] |
| GUARDED − HYBRID | **0.00** | **[0, 0]** | **0.00** | **[0, 0]** |
| BLIND − OFF | +0.57 | [+0.08, +1.14] | +0.57 | [−0.16, +1.85] |

No evidence that GUARDED beats HYBRID on held-out (exact tie). BLIND is slightly ahead on mean, driven largely by Q19.

---

## 14. Evidence Guard Performance

| Metric | Held-out |
|---|---:|
| Skips | **0** |
| Expands | **20** |
| True-positive skips | 0 |
| False-positive skips | **0** |
| True-negative expands | 2 |
| False-negative expands | **18** |

Offline oracle = “all primary chunks already in semantic hits.”

**What this means:** The guard almost never recognized “already enough evidence” on held-out items, even when retrieval already contained the primary chunks. Need classification fell through to `general` for most questions (how-much / when / what-is fact patterns), and the conservative general path chose **expand**.

It did **not** falsely skip when evidence was incomplete (0 FP skips)—safe, but too timid to recreate Step 8 gains.

---

## 15. Context Efficiency

| Config | Mean chars | Mean neighbors | Mean irrelevant neighbors |
|---|---:|---:|---:|
| OFF | 4359 | 0.00 | 0.00 |
| BLIND | 6812 | 4.85 | 4.75 |
| HYBRID / GUARDED | 4916 | 1.00 | 1.00 |

Guarded did **not** reduce context vs HYBRID on held-out (identical expansion).

---

## 16. False-Positive / False-Negative Analysis

- **FP skips:** none — good safety property preserved.  
- **FN expands:** 18/20 — guard expands despite oracle-sufficient retrieval.  
- Categories with FN expand include most single-chunk numerical facts.  
- TN expand: Q18, Q19 (primary incomplete in top-5) — correct to allow expansion; however HYBRID/GUARDED still failed Q19 utilization while BLIND succeeded.

---

## 17. Difficult Question Analysis

**Q19 (ticket statuses):** OFF/HYBRID/GUARDED mean 16; BLIND 28.  
Neighbor/hybrid context did not surface usable status labels for the checklist scorer; blind ±1 did. This shows expansion strategy quality is not just “add neighbors,” but *which* neighbors and how the model uses them.

**Q13:** HYBRID/GUARDED improved over OFF/BLIND on stating the not-activated condition.

Ceiling effect elsewhere limited discrimination.

---

## 18. Limitations

1. Held-out items are mostly short factual lookups → high scores, weak sensitivity.  
2. n=20 questions is still small for confirmatory claims.  
3. Checklist scoring differs from Step 3/8 human-style notes (same 0–4 metrics, fact-needle mapping).  
4. Guard need taxonomy under-covers “how much / what is the X” fact questions → expand-always behavior.  
5. Development comparison uses archived Step 8 runs (same seeds/settings, different day) — absolute scores not pooled.  
6. No production recommendation from either Step 8 or Step 9 alone.

---

## 19. Final Recommendation

### Verdict: **DOES NOT GENERALIZE**

The Step 8 GUARDED advantage **does not transfer** to this held-out battery:

1. Guard skip rate collapses from 3/7 (dev) to **0/20** (held-out).  
2. GUARDED ≡ HYBRID on every held-out aggregate and paired contrast.  
3. BLIND is slightly better on held-out mean (mainly Q19).  
4. Zero FP skips is reassuring, but **over-expansion** (FN expands) means the guard is not delivering the selective benefit that made Step 8 look promising.

**Do not deploy** guarded hybrid to production based on Steps 8–9.

**If continuing research (approval required):** redesign need coverage for factual/numerical questions **without peeking at Q8–Q27 labels during implementation**, then validate on a *new* third split. Optionally build a harder held-out set (more Q19-like multi-chunk utilization failures). Do **not** retune the frozen Step 8 guard against Q8–Q27.

---

## Files Created (experiment only)

| File | Role |
|---|---|
| `heldout_dataset.py` | Q8–Q27 questions + offline annotations |
| `heldout_answer_key.py` | Offline expected facts |
| `heldout_annotations.py` | Annotation helpers |
| `heldout_scoring.py` | Checklist scoring for held-out |
| `run_heldout_eval.py` | Frozen-guard 4-config runner |
| `test_heldout_dataset.py` | Dataset / leakage / freeze tests |
| `step9_heldout/heldout_results.json` | Machine-readable results |
| `HELDOUT_GENERALIZATION_REPORT.md` | This report |

## Unchanged Confirmation

Production code, prompts, defaults, DB, embeddings, Q1–Q7 ground truth, Step 8 guard implementation/hash, and Step 8 reports/results were **not** modified.

**Stop.** Awaiting review.
