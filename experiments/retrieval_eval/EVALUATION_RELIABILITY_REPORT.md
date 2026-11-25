# Phase 4.2 P1 Step 7 — Evaluation Reliability and Statistical Analysis

**Verdict:** **EVALUATION NOT YET RELIABLE ENOUGH FOR PRODUCTION DECISIONS**  
**Mode:** Investigation / analysis only (no production or score changes)  
**Primary data:** Step 6 multi-seed run (`seeds=101,202,303`)  
**Stats artifact:** `evaluation_reliability_stats.json`

---

## 1. Executive Summary

Observed mean differences among neighbor-expansion strategies are **small relative to answer variance**, and **one question (Q6)** can reverse selective-vs-blind rankings. With 3 seeds × 7 questions, the sample cannot support confirmatory “strategy A beats B” claims.

| Finding | Status |
|---|---|
| Same Step 3 rubric family used across Steps 3/5/6 | Confirmed |
| Step 6 scoring was configuration-aware checklist automation (not blind) | Confirmed limitation |
| BLIND − OFF mean Δ ≈ +1.1 /28; bootstrap 95% CI crosses 0 | Descriptive only |
| HYBRID_CAP2 − BLIND mean Δ ≈ −0.6 /28; CI crosses 0; dominated by Q6 (−12) | Descriptive only |
| Step 5 C=25.0 not replicated under multi-seed | Confirmed |
| Q6 selective regression: competing restocking-fee neighbor + seed-sensitive generation | Confirmed mechanism (see §5) |
| Seed makes same request reproducible; different seeds still diverge on full RAG prompts | Confirmed |
| Q1–Q7 coverage has material gaps (abstention, multi-doc conflict, exceptions) | Confirmed |

**Bottom line:** Treat Steps 3–6 as **directional diagnostics**, not as a ranked bake-off for production. Next work should harden evaluation reliability (paired design, Q6-focused regression gate, optional modest seed increase *after* fixing the known failure mode)—not ship HYBRID/C/BLIND based on current means.

---

## 2. Scoring Methodology Audit

### 2.1 Rubric consistency

| Step | Scorer | Rubric | Evidence per cell |
|---|---|---|---|
| Step 3 | Human | Seven 0–4 metrics (documented in `ANSWER_LEVEL_EVALUATION_REPORT.md`) | Written rationales in `answer_level_eval_scores.json` |
| Step 5 | Human | Same seven metrics | Notes in `selective_expansion_scores.json` |
| Step 6 | Checklist-assisted (`hybrid_scoring.py`) | Same metric names/scale; mapped via question-specific phrase checks | `note` fields + answer previews in `hybrid_expansion_stability_scores.json` |

**Confirmed:** Metric definitions (including `unsupported_claims`: higher = fewer claims) were not redesigned between steps.  
**Confirmed:** Absolute totals still differ across steps mainly because **answers** differ, not because the rubric schema changed.

### 2.2 Blindness to configuration labels

| Step | Blind scoring? |
|---|---|
| Step 3 | **No** — OFF/ON labeled in the score artifact; human knew mode when scoring |
| Step 5 | **No** — scored by config name (OFF/BLIND/A/B/C) |
| Step 6 | **No** — automated scorer receives `query_id` + answer + context metadata; configs are scored in labeled loops |

**Limitation:** Non-blind scoring can inflate apparent differences. Step 6’s checklist reduces some subjectivity but **embeds prior hypotheses** (e.g. Q6 soft-miss → total 10; Q1 methods+cutoff → 25).

### 2.3 Subjectivity / ambiguity

Ambiguous or judgment-heavy areas (do not re-score here):

1. **Overnight wording** (“1 business day” vs “Next business day”) — sometimes minor correctness penalty historically.
2. **Expedited vs Express** synonym acceptance in Step 6 checklist.
3. **Q5 “contact support”** — listing ticket categories vs listing ticket fields; checklist favors category lists.
4. **Q2 collapsed one-liners** vs full 3-step lists — large score swing (20 vs 28) from utilization/completeness.
5. **Partial credit** for conditions when evidence is present but underused — evidence_utilization vs completeness can double-count the same omission.

### 2.4 Do Q1–Q7 cover distinct RAG behaviors?

| Behavior | Covered by | Adequacy |
|---|---|---|
| Table completion | Q1, Q5 | Good |
| Numbered procedure | Q2, Q7 | Good |
| Eligibility / overdue + refund | Q3 | Good |
| Conditions (15:00, 7-day lost) | Q1, Q2, Q3 | Partial |
| Distributed evidence (multi-chunk) | Q1, Q3, Q4 | Good |
| Multi-document | Q3 (delivery+refund) | Thin (one item) |
| Incomplete / truncated context | Q1, Q4, Q5 | Good |
| Abstention when evidence missing | — | **Gap** |
| Explicit exceptions / non-eligibility | Q3 soft | **Gap** |
| Conflicting neighboring text | Q6 (emergent) | Accidental, not designed |

**Conclusion:** The seven questions are useful smoke tests for expansion, but they are **not** a balanced reliability battery. One fragile cell (Q6) can dominate strategy ranking.

---

## 3. Statistical Analysis

Source: Step 6 scores only (`n=21` cells per config = 7 questions × 3 seeds).  
Population std in prior report ≈ sample descriptive std here; both reported in `evaluation_reliability_stats.json`.

### 3.1 Config-level descriptive statistics

| Config | Mean | Median | Std (pop) | Std (sample) | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| OFF | 22.333 | 21 | 3.834 | 3.929 | 17 | 28 |
| BLIND | 23.429 | 23 | 3.260 | 3.340 | 18 | 28 |
| A_TABLE | 22.095 | 23 | 5.098 | 5.224 | 10 | 28 |
| C_EVIDENCE | 22.000 | 23 | 4.995 | 5.119 | 10 | 28 |
| HYBRID_CAP2 | 22.857 | 23 | 5.007 | 5.131 | 10 | 28 |
| HYBRID_CAP3 | 22.000 | 23 | 4.995 | 5.119 | 10 | 28 |

Selective strategies show **higher dispersion** (min 10 from Q6 failures). BLIND has the highest mean and lowest spread among expanding configs.

### 3.2 Per-question mean and seed SD (population)

| Q | OFF μ (σ) | BLIND | A | C | HYB2 | HYB3 |
|---|---|---|---|---|---|---|
| Q1 | 19.7 (1.9) | 22.3 (1.9) | 23.7 (1.9) | 23.7 (1.9) | 23.7 (1.9) | 23.7 (1.9) |
| Q2 | 22.7 (3.8) | 20.0 (0.0) | 22.7 (3.8) | 22.7 (3.8) | 22.7 (3.8) | 22.7 (3.8) |
| Q3 | 19.0 (1.4) | 20.7 (2.1) | 19.0 (1.4) | **24.7 (2.4)** | **24.7 (2.4)** | **24.7 (2.4)** |
| Q4 | 26.0 (0) | 26.0 (0) | 26.3 (0.5) | 26.0 (0) | 26.0 (0) | 26.0 (0) |
| Q5 | 18.0 (0) | 24.0 (4.2) | 24.0 (4.2) | 18.0 (0) | 24.0 (4.2) | 18.0 (0) |
| Q6 | **28.0 (0)** | **28.0 (0)** | **16.0 (8.5)** | **16.0 (8.5)** | **16.0 (8.5)** | **16.0 (8.5)** |
| Q7 | 23.0 (0) | 23.0 (0) | 23.0 (0) | 23.0 (0) | 23.0 (0) | 23.0 (0) |

Q4/Q7 are stable. Q2/Q5/Q6 drive uncertainty. Q6 alone moves selective means by ~12 points on failing seeds.

### 3.3 Dependence caveat

The 21 cells per config are **not i.i.d.**:

- Same question shares identical retrieval hits and (within config) identical CONTEXT across seeds.
- Seeds only vary the generation draw.
- Questions are few and unequal in difficulty/variance.

Therefore: do **not** interpret “n=21” as 21 independent A/B trials. Prefer question-level summaries (n=7) plus explicit per-question regression tracking.

---

## 4. Paired Comparison

Matched on `(question, seed)`. Effect size = Cohen’s \(d_z\) = mean(diff) / sd(diff).  
Bootstrap 95% CI for mean diff (5000 resamples; descriptive). **No p-value / “significant” claims.**

### 4.1 Cell-level paired diffs (n=21)

| Contrast | Mean Δ | Median Δ | \(d_z\) | Boot 95% CI | Signs (+/−/0) |
|---|---:|---:|---:|---|---|
| BLIND − OFF | +1.10 | 0 | 0.29 | [−0.43, +2.71] | 5 / 1 / 15 |
| HYBRID_CAP2 − OFF | +0.52 | 0 | 0.07 | [−2.81, +3.43] | 9 / 3 / 9 |
| HYBRID_CAP2 − BLIND | −0.57 | 0 | −0.08 | [−3.71, +2.14] | 6 / 4 / 11 |
| HYBRID_CAP2 − C_EVIDENCE | +0.86 | 0 | 0.32 | [0.00, +2.14] | 2 / 0 / 19 |
| C_EVIDENCE − BLIND | −1.43 | 0 | −0.21 | [−4.48, +1.24] | 5 / 5 / 11 |
| HYBRID_CAP3 − HYBRID_CAP2 | −0.86 | 0 | −0.32 | [−2.14, 0.00] | 0 / 2 / 19 |

**Interpretation:** Most CIs include 0 or touch 0. Point estimates favor BLIND slightly over OFF/C, and CAP2 slightly over C (driven almost entirely by Q5). Effect sizes are **small**, except where Q6 creates large negative outliers for selective arms.

### 4.2 Question-mean paired diffs (n=7)

| Contrast | Mean Δ | \(d_z\) | Boot 95% CI | Notable per-Q Δ |
|---|---:|---:|---|---|
| BLIND − OFF | +1.10 | 0.40 | [−0.76, +2.95] | Q5 +6; Q2 −2.7 |
| HYBRID_CAP2 − OFF | +0.52 | 0.09 | [−4.29, +3.95] | Q1+4, Q3+5.7, Q5+6, **Q6 −12** |
| HYBRID_CAP2 − BLIND | −0.57 | −0.11 | [−4.76, +2.29] | Q3 +4; **Q6 −12** |
| C_EVIDENCE − BLIND | −1.43 | −0.25 | [−5.62, +2.00] | Q3 +4; Q5 −6; **Q6 −12** |
| HYBRID_CAP2 − C | +0.86 | 0.38 | [0.00, +2.57] | **Q5 +6 only** |

**Confirmed:** HYBRID_CAP2’s advantage over C is **not general** — it is a Q5 utilization difference under the current checklist.  
**Confirmed:** Any claim that selective expansion beats BLIND on mean quality is **not supported** once Q6 is included.

---

## 5. Q6 Investigation (HYBRID_CAP2)

Question: *What evidence is required for defective products?*  
Primary GT: `refund_policy.md#1` (photographic evidence / support ticket).

### 5.1 Confirmed facts

1. **Semantic hits (identical across configs):**  
   `refund_policy.md#2`, `#6`, `#1`, `product_documentation.md#3`, `#6`.  
   Primary `#1` is retrieved and listed in `primary_in_context` for OFF and HYBRID_CAP2.

2. **HYBRID_CAP2 neighbors (same for all seeds):**
   - `refund_policy.md#3` — `truncated_table_next` from `#2` (order-status table continuation → refund methods).
   - `refund_policy.md#5` — `truncated_evidence_previous` from `#6` (partial refunds / **restocking fee** section).

3. **Evidence available in CONTEXT:** Photo/ticket requirement remains present via retrieved `#1` (and overlapping `#2` head). Neighbor `#5` adds: *“No restocking fee applies for defective, damaged, or incorrectly shipped items.”* — related topic word (“defective”) but **different claim**.

4. **Answers across seeds (HYBRID_CAP2):**
   - Seed **101**: Correct photo/ticket answer → total **28**.
   - Seeds **202** and **303**: Cite restocking-fee wording / “without defect…” and omit or deny specific evidence → total **10** each.

5. **Consistency of regression:** Same 28/10/10 pattern for **A_TABLE, C_EVIDENCE, HYBRID_CAP2, HYBRID_CAP3**. OFF and BLIND stay **28/28/28**. So the failure is **selective-expansion-associated**, not universal model failure on Q6.

6. **Context construction:** Built once per `(question, config)`; seeds only change generation. Retrieval and neighbor sets do **not** change across seeds.

### 5.2 Confirmed mechanism (supported by chunk text)

Neighbor `#5` contains restocking-fee language that **mentions defective items** without restating the photographic-evidence rule. Failing answers quote that competing span (e.g. “without defect. No restocking fee…”), i.e. **attention/utilization error under expanded context**, not missing primary retrieval.

A_TABLE additionally attaches `product_documentation.md#7` (unrelated table continuation) — still shows the same 2/3 seed failure, so product-doc neighbor is not required for the bug.

### 5.3 Hypotheses (not proven)

1. Mid-chunk / mid-sentence neighbor boundaries increase the chance the model treats the restocking block as the answer span.
2. Larger selective context (5653 vs 4455 chars) raises underuse risk even when the correct sentence remains present (consistent with Step 4 root-cause theme).
3. BLIND also adds `#3`/`#5` (and more) but still answers correctly — **hypothesis:** extra redundant restatements of photo evidence elsewhere in the larger BLIND context, or different block ordering, stabilize generation; not isolated in this audit.

### 5.4 Implication

Q6 is a **real regression signal** for current selective heuristics (2/3 seeds), not a one-off scorer quirk. Any production candidate must include an explicit **Q6 (or “required evidence already present”) gate**.

---

## 6. Generation Variability Analysis

### 6.1 Production vs experiment path

| Path | Temperature | Seed |
|---|---|---|
| Production `OllamaProvider.chat` | Passed in `options.temperature` (RAG uses `0.2`) | **Not passed** |
| Step 6 experiment harness | `0.2` in `options` | `options.seed` set per run |

**Confirmed:** Temperature is applied on both paths. Seed is **only** applied in the experiment harness.

### 6.2 Determinism checks

| Test | Result |
|---|---|
| Same seed + same prompt repeated | **Identical** completion (verified pre-Step 6 and rechecked on Q6-like prompt) |
| Different seeds on short/simple prompt | Often identical (low entropy) |
| Different seeds on full Step 6 RAG contexts | **Frequently different** (Step 6: most Q×config cells had 3 unique answers) |
| No seed, two calls | Can match or differ; production path is uncontrolled |
| Retrieval across configs (fixed question) | **Identical** (`semantic_hits_identical_across_configs=true`) |
| Context across seeds (fixed question×config) | **Identical** (built once) |

**Confirmed:** Setting a seed makes a *given* request reproducible, but **does not make the model deterministic across seeds**, and does not remove quality variance at `temperature=0.2`.  
**Do not assume** seed control alone yields stable strategy rankings.

### 6.3 Cross-run absolute score drift

| Run | OFF mean |
|---|---:|
| Step 3 | 24.0 |
| Step 5 | 21.0 |
| Step 6 | 22.3 |

Same rubric family and settings; different answer draws. **Confirmed:** absolute means are not interchangeable across experimental batches.

---

## 7. Dataset Coverage Assessment

### 7.1 What Q1–Q7 cover well

- Truncated shipping **table** (Q1)
- Overdue / lost-package **procedure** (Q2)
- Cross-policy **eligibility** wording (Q3)
- Truncated PTO bullet (Q4)
- Support **categories** table (Q5)
- Defective-product **evidence** fact (Q6)
- Refund **process** steps (Q7)

### 7.2 Coverage gaps (recommend separately; do not change GT now)

| Gap | Why it matters |
|---|---|
| **Abstention** (“not in documents”) | Current set rarely rewards saying “insufficient evidence” |
| **Hard exceptions / non-refundable** | Weak pressure to preserve exclusions |
| **Multi-doc conflict** | Only light multi-doc; no designed contradiction |
| **Privacy / security policy** | Corpus docs exist but unevaluated at answer level |
| **Numeric edge cases** (windows, fees) | Sparse |
| **Neighbor distraction probes** | Q6 emerged accidentally; need deliberate distractor items |
| **Empty / low-similarity retrieval** | No dedicated item |

Suggested *future* add-ons (names only; not added here): Q8 abstention, Q9 non-refundable exception, Q10 damaged-in-transit 48h photo rule, Q11 privacy retention, Q12 intentional distractor-neighbor stress.

---

## 8. Statistical Limitations

1. **n_seeds=3**, **n_questions=7** — underpowered for strategy bake-offs.
2. Cells within a question are dependent (shared retrieval/context).
3. Checklist scoring is labeled and hypothesis-informed (not blind double-rating).
4. Bootstrap CIs are **exploratory**; they do not fix dependence or small-n issues.
5. Mean totals weight all questions equally; Q6 failures dominate selective rankings.
6. Context-efficiency is not folded into the scalar score (BLIND can “win” mean quality while using ~1.5× characters).
7. No inter-rater reliability (κ) for human Steps 3/5.

---

## 9. Recommended Next Experiment

**Do not** only “add more seeds” on the current HYBRID_CAP2 — that mainly re-estimates the same Q6 failure rate and burns generations without fixing the known mechanism.

### Recommended Step 8 design (experiment-only)

**Name:** Guarded hybrid paired validation  

1. **Intervention (experiment planner only):** HYBRID_CAP2 **plus** a Q6-style guard:  
   if primary retrieved text already contains the key evidence phrase (e.g. photographic evidence), **do not** expand neighbors for that question / hit cluster.  
   Keep A∪C hybrid otherwise, cap=2.

2. **Arms:** OFF, BLIND, HYBRID_CAP2 (ungarded, frozen reference), HYBRID_CAP2_GUARDED.

3. **Design:** Paired on `(question, seed)`. Use **5 seeds** *after* the guard exists — expected value: estimate residual Q6 fail rate and tighten CIs on Q1/Q3/Q5 deltas, not to discover the Q6 bug again.

4. **Primary endpoints (pre-registered):**
   - Per-question mean Δ vs OFF and vs BLIND  
   - **Hard gate:** Q6 mean(guarded) ≥ Q6 mean(OFF) − 1  
   - Mean context chars / neighbor count  
   - No claim of overall superiority unless Q6 gate passes **and** question-level wins are not confined to a single item

5. **Scoring:** Keep Step 3 rubric; add **blind** pass for disputed cells (hide config labels). Optionally dual-score Q2/Q5/Q6 only.

6. **Dataset:** Keep Q1–Q7 unchanged; optionally *append* 2–3 new questions in a separate “extended” slice so baselines remain comparable.

7. **Evaluator consistency:** Freeze checklist rules in a versioned file; sample 20% human audit.

**Why not only more seeds first?** Extra seeds without the Q6 guard will likely reconfirm ≈2/3 selective failures and leave the production decision unchanged while increasing cost.

---

## 10. Final Verdict

### **EVALUATION NOT YET RELIABLE ENOUGH FOR PRODUCTION DECISIONS**

| Question | Answer |
|---|---|
| Are strategy mean gaps meaningful? | **Not established.** Small effects; CIs cross 0; Q6 dominates. |
| Is HYBRID_CAP2 ready? | **No** — best selective candidate, blocked by Q6 regression. |
| Was C_EVIDENCE’s 25.0 reliable? | **No** — single-run artifact. |
| Is BLIND clearly better quality? | **Suggestive on mean, not proven;** much worse context efficiency. |
| Can we ship any expansion change now? | **No.** |

### Files created (analysis only)

| File | Role |
|---|---|
| `experiments/retrieval_eval/run_evaluation_reliability_analysis.py` | Read-only stats harness |
| `experiments/retrieval_eval/evaluation_reliability_stats.json` | Descriptive + paired stats + Q6 snapshot |
| `experiments/retrieval_eval/EVALUATION_RELIABILITY_REPORT.md` | This report |

### Unchanged confirmation

Production code, prompts, configuration defaults, semantic search, neighbor expansion, chunking, database records, embeddings, Q1–Q7 ground truth, prior baselines, and existing Step 3/5/6 scores were **not** modified.

**Stop.** Awaiting approval before any next experiment or production work.
