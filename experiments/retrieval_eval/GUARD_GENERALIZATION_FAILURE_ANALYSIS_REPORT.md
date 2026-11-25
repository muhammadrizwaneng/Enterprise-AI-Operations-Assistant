# Step 10 — Guard Generalization Failure Analysis

**Mode:** READ-ONLY investigation (no code, data, or experiment changes)  
**Verdict labels used below:** CONFIRMED / LIKELY / UNCONFIRMED / INSUFFICIENT DATA  

**Primary artifacts:**  
`evidence_guard.py` (frozen SHA-256 `4ab51eb2…eae6`),  
`step8_guarded_hybrid/guarded_hybrid_results.json`,  
`step9_heldout/heldout_results.json`,  
Step 8/9 reports.

---

## 1. Executive Summary

In plain English: the Step 8 guard looked smart on a **small, specially worded** development set. On held-out questions, it almost always fell into a **catch-all “GENERAL” path** that treats “any truncated chunk in the top-5” as incompleteness—and therefore **always expands**. So GUARDED became identical to HYBRID.

| Finding | Label |
|---|---|
| Dev skips (3/7) happened only when questions matched narrow keyword need classes **and** specialized sufficiency checks passed | **CONFIRMED** |
| Held-out: **19/20** classified as `general`; **0/20** skipped | **CONFIRMED** |
| GENERAL path fails sufficiency whenever *any* top-5 hit is truncated/incomplete—even if the answering chunk is already complete | **CONFIRMED** |
| Main failure = **both** classification coverage gap **and** overly conservative GENERAL sufficiency | **CONFIRMED** |
| Q19 Blind win is real and consistent across 5 seeds; selective hybrid picked the **wrong** neighbors | **CONFIRMED** |
| Blind expansion is therefore helpful for *some* neighbor-gap questions—not proven generally superior | **CONFIRMED** (scoped) |

**Bottom line:** The guard did not “forget how to skip.” Its skip rules only fire for a few question phrasings. Most realistic fact questions never enter those rules, then fail a truncation-based GENERAL check.

---

## 2. Step 9 Failure Recap

| Metric | Dev Q1–Q7 (Step 8) | Held-out Q8–Q27 (Step 9) |
|---|---:|---:|
| GUARDED mean | 24.11 | 27.35 |
| HYBRID mean | 22.34 | 27.35 |
| Guard skips | **3/7** | **0/20** |
| GUARDED vs HYBRID | Better | **Exact tie** |
| Best held-out mean | — | BLIND 27.84 (largely Q19) |

---

## 3. Existing Guard Architecture

### 3.1 Two-stage design (simple English)

1. **Classify the question type** from wording only (regex keywords).  
2. **Check retrieved chunk text** with a type-specific rule.  
3. If “sufficient” → skip expansion; else → run HYBRID_CAP2.

Default when unsure: **expand** (`INSUFFICIENT`). Documented in `evidence_guard.py` lines 11–12 and 354–379.

### 3.2 Need classification (`classify_evidence_need`)

| Need | Keyword triggers (examples) |
|---|---|
| `requirement_evidence` | `evidence`, `what … required`, `required … for` |
| `contact_support` | `how do/can I contact/reach`, or “customer support” + “contact” |
| `duration_table` | `how long`, `transit time`, `delivery take` |
| `eligibility` | `can i`, `eligible`, `refund if`, `late delivery` |
| `procedure` | `what happens`, `process`, `procedure`, `steps`, `overdue`, `if a package` |
| `general` | **everything else** |

This is deterministic keyword/heuristic logic—not an LLM, not embeddings.

### 3.3 Sufficiency checks → skip vs expand

| Need | Skip if… | Expand if… |
|---|---|---|
| requirement_evidence | Hit has topic overlap + require/must/supported-by language | No such statement |
| procedure | ≥3 numbered steps / complete “Support agents must” list | Incomplete procedure signals |
| duration_table | Complete multi-method duration table | Any incomplete/truncated table in hits |
| eligibility | Overdue def + lost-package rule when needed | Definition without 7-day rule, etc. |
| contact_support | Single-chunk category table with ≥3 categories | Incomplete / missing category listing |
| **general** | Lexical coverage ≥ 0.6 **and** **no** incompleteness signals on **any** hit | Otherwise (default) |

**GENERAL incompleteness signals** (any hit): truncated chunk, incomplete table, or procedure-needs-next (`evidence_guard.py` 364–369).

### 3.4 Is it overly conservative?

**CONFIRMED — yes, on the GENERAL path.**  
Even with lexical coverage 0.75–1.00, held-out questions still expand because *other* top-5 chunks are 500-char window truncations. The guard confuses “some retrieved text is cut mid-window” with “the answer is incomplete.”

---

## 4. Development Dataset Analysis (Q1–Q7)

Data from `step8_guarded_hybrid/guarded_hybrid_results.json`.

| Q | Need | Primary in hits? | Guard | Reason (recorded) | Justified? |
|---|---|---|---|---|---|
| Q1 | `duration_table` | Partial (#1 yes, #2 no) | **EXPAND** | incomplete/truncated table | **Yes** — methods table incomplete |
| Q2 | `procedure` | Yes (#4,#5) | **SKIP** | support_agents_must_with_3_plus_steps | **Yes** — full 3-step list present |
| Q3 | `eligibility` | Partial (#5 missing) | **EXPAND** | overdue def without lost-package rule | **Yes** |
| Q4 | `general` | Yes | **EXPAND** | coverage 0.50 + incompleteness | Weak — FN expand vs oracle; hybrid planned 0 neighbors anyway |
| Q5 | `contact_support` | Partial (#1 missing) | **EXPAND** | category_table_incomplete | **Yes** |
| Q6 | `requirement_evidence` | Yes (#1) | **SKIP** | requirement_statement_in_refund_policy.md#1 | **Yes** — avoids #5 distraction |
| Q7 | `procedure` | Yes (#6) | **SKIP** | numbered_steps_count=9 | **Yes** — refund steps already present |

### The three skips (why they worked)

1. **Q6** — Question contains `evidence` + `required` → specialized requirement checker finds photo/ticket language in retrieved `#1`.  
2. **Q2** — `what happens` + `overdue` → procedure checker finds complete agent steps in `#5`.  
3. **Q7** — `process` → procedure checker finds numbered refund steps in `#6`.

**CONFIRMED:** Dev skips are concentrated in need classes that match the **phrasing style** of Q2/Q6/Q7, not a general “detect enough facts” ability.

---

## 5. Held-Out Dataset Analysis (Q8–Q27)

Data from `step9_heldout/heldout_results.json` + live re-check of truncation (read-only).

| Pattern | Count |
|---|---:|
| Classified `general` | **19/20** |
| Classified `duration_table` | **1/20** (Q24: “How long…”) |
| Skips | **0/20** |
| Expand reason includes `incompleteness_signals` or truncated table | **20/20** |
| Oracle: all primary already in hits, but still expanded (FN expand) | **18/20** |
| Oracle incomplete (TN expand) | **2/20** (Q18, Q19) |

### Recurring failure pattern (CONFIRMED)

1. Question is “What is / How much / When / How soon …” → **no keyword match** → `general`.  
2. Lexical coverage often **high** (0.75–1.00).  
3. Top-5 almost always contains **some other** 500-char truncated chunk.  
4. GENERAL rule: any truncation ⇒ insufficient ⇒ **expand**.  
5. HYBRID may add 0–2 neighbors (sometimes irrelevant); GUARDED does the same.

Examples of FN expand (answerable facts already in hits):

- Q9 `$9.99` in `#3`, still expand (truncation elsewhere).  
- Q12 `30 calendar days` in `#1`, still expand.  
- Q14 `15%` in `#5`, still expand.  
- Q23 `7 years` in `#4`, still expand (and `#4` itself flagged truncated/incomplete table).

TN expand (genuinely incomplete retrieval of annotated primaries):

- Q18 missing `#7`  
- Q19 missing `#4`

---

## 6. Development vs Held-Out Comparison

| Dimension | Dev Q1–Q7 | Held-out Q8–Q27 |
|---|---|---|
| Dominant need classes | Mixed specialized (6/7 non-general) | **GENERAL (19/20)** |
| Skip rate | 43% (3/7) | **0%** |
| Question style | process / evidence / how long / can I | factoid “what/how much/when” |
| Mean scores | Mid-20s (harder utilization) | ~27–28 (ceiling) |
| Guard value vs HYBRID | Material (esp. Q6) | **None** |

**CONFIRMED:** The datasets differ sharply in **surface phrasing**, which drives classification coverage—not only in “difficulty.”

---

## 7. Classification Coverage Analysis

| Need class | Dev hits | Held-out hits |
|---|---:|---:|
| requirement_evidence | 1 (Q6) | 0 |
| procedure | 2 (Q2,Q7) | 0 |
| duration_table | 1 (Q1) | 1 (Q24) |
| eligibility | 1 (Q3) | 0 |
| contact_support | 1 (Q5) | 0 |
| general | 1 (Q4) | **19** |

**CONFIRMED — classification coverage problem exists.**  
The keyword taxonomy was effectively fitted to the *kinds of questions* in Q1–Q7. Held-out fact questions do not say “evidence,” “process,” “what happens,” or “how long does delivery take,” so they never enter the specialized skip paths.

**Also CONFIRMED — sufficiency problem exists inside GENERAL** (next section). So it is **both**, not either/or.

Note: Q10 contains the word “require” but classifier needs `required`/`evidence` patterns—so it still becomes `general`. **CONFIRMED** brittle lexical matching.

---

## 8. Evidence Sufficiency Analysis

### Concepts the guard mixes up

| Concept | Meaning | Guard behavior |
|---|---|---|
| Retrieval relevance | Chunk is topically related | Not directly scored; uses top-5 as given |
| Evidence completeness | All *needed* facts present | Specialized checkers approximate this |
| Evidence sufficiency | Enough to answer without neighbors | Intended goal |
| Answerability | Model can produce correct answer from context | Not measured by guard |

### Cases: sufficient original context, still expand

**CONFIRMED** for 18 held-out FN expands (oracle: all primary labels in hits).  
Mechanism: GENERAL incompleteness over *any* truncated neighbor in the hit list—not over the answering span.

### Cases: expansion genuinely necessary

| Q | Why | Did HYBRID/GUARDED help? |
|---|---|---|
| Q1 (dev) | Methods table `#2` missing | Yes (table neighbor) |
| Q3 (dev) | `#5` 7-day rule missing | Yes |
| Q5 (dev) | Category table `#1` missing | Partial |
| Q18 (held-out) | `#7` missing | Mixed; neighbors not ideal |
| **Q19 (held-out)** | `#4` statuses missing | **HYBRID/GUARDED failed**; **BLIND succeeded** |

---

## 9. Q19 Deep Investigation

**Question:** “What ticket status values are used in the support workflow?”  
**Primary evidence:** `customer_support_guidelines.md#3` (starts status list) + `#4` (continues with resolved/closed).

### Retrieval

Top-5 includes `#3` but **not** `#4` (oracle incomplete). Guard → expand (TN expand). **CONFIRMED** justified *decision to expand*.

### What each config added

| Config | Neighbors affecting statuses | `#4` in context? | Mean score (5 seeds) |
|---|---|---|---:|
| OFF | none | No | **16** (all seeds) |
| BLIND | includes `#3→next = #4` | **Yes** | **28** (all seeds) |
| HYBRID | `refund_policy.md#3`, `guidelines.md#2` (wrong tables) | **No** | **16** (all seeds) |
| GUARDED | same as HYBRID | **No** | **16** (all seeds) |

### Answer behavior

- OFF/HYBRID/GUARDED answers list **open / in_progress / waiting_customer** but miss **resolved / closed** (those live in `#4`). Score note: `facts=1/3` with `#4` missing.  
- BLIND answers include full set → 28.

### Consistency

Totals `[16,16,16,16,16]` vs `[28,28,28,28,28]` — **not** seed noise. **CONFIRMED** stable effect.

### Interpretation

**CONFIRMED:** Blind ±1 on the hit that *starts* the truncated status section (`#3`) is the right structural move. Selective hybrid’s table/truncation heuristics expanded **other** hits’ neighbors instead of `#3+1`.

**CONFIRMED (scoped):** Blind can help **certain neighbor-gap questions**.  
**Not confirmed:** Blind is generally best (uses ~1.5× context; loses on other items historically).

---

## 10. Statistical Findings

From recorded Step 9 aggregates/paired contrasts (no new stats invented):

| Contrast (held-out) | Mean Δ | Notes |
|---|---:|---|
| GUARDED − HYBRID | **0.00** | Exact behavioral twin |
| GUARDED − OFF | +0.08 | Tiny; CI touches 0 |
| GUARDED − BLIND | −0.49 | Driven heavily by Q19 (−12 on that question mean) |
| BLIND − OFF | +0.57 | Also Q19-dominated |

**CONFIRMED:** Held-out strategy ranking is dominated by a **small number of questions** (especially Q19), under a high ceiling (~28).

Dev Step 8 GUARDED advantage was likewise concentrated (Q6 skip + selective Q1/Q3), not uniform.

---

## 11. Confirmed Root Causes

1. **Narrow need taxonomy** — skip-capable classes require specific keywords common in Q1–Q7, rare in Q8–Q27.  
2. **GENERAL path is expand-by-default** when any top-5 chunk is truncated—almost always true with 500-char windows.  
3. **Confusion of chunk truncation with answer insufficiency** — high lexical coverage still expands.  
4. **Selective hybrid ≠ correct neighbor selection** — Q19 expands the wrong origins; Blind’s ±1 on the right hit wins.  
5. **Step 8 success was brittle** — largely Q6-style requirement phrasing + procedure phrasing, not a general sufficiency detector.

---

## 12. Possible Root Causes Requiring Further Validation

| Hypothesis | Label |
|---|---|
| A richer need taxonomy for “what/how much/when” factoids would restore skips without hurting Q1/Q3 | **LIKELY** (not tested; must not tune on Q8–Q27) |
| Sufficiency should inspect only top-1 / best-matching hit, not all top-5 truncations | **LIKELY** |
| Embedding retrieval + min_similarity interacts with which truncated distractors appear | **UNCONFIRMED** |
| Held-out ceiling effect hides small guard benefits | **LIKELY** for mean discrimination; does **not** erase the 0-skip fact |

---

## 13. Why the Guard Failed to Generalize

**Simple English:**  
It learned (by design) to recognize a few question “shapes.” The new questions were different shapes. For those, it used a timid backup rule: “If anything in the search results looks cut off, ask for more neighbors.” With fixed-size chunks, something almost always looks cut off—so it never skipped.

Therefore GUARDED ≡ HYBRID on held-out, and the Step 8 story (especially Q6) did not transfer.

---

## 14. What We Learned

1. A keyword need classifier can look strong on a tiny prompt-similar set and collapse off-distribution.  
2. “Conservative expand” without a good sufficiency test becomes “always expand.”  
3. Measuring skip rate on a second split is essential before trusting a guard.  
4. Neighbor expansion quality depends on **which** neighbor—Blind can beat selective heuristics when heuristics fire on the wrong hit (Q19).  
5. High held-out means do not imply a good guard; they can mean easy questions + ceiling.

---

## 15. Recommendations for the Next Experiment

**Do not implement here.** Single most logical next experiment:

### Proposed Step 11 — Controlled ablation of GENERAL sufficiency (new held-out split)

**Goal:** Separate classification coverage vs truncation-triggered over-expansion **without** tuning on Q8–Q27 labels.

1. Freeze current guard as baseline G0.  
2. Build a **new** held-out split H2 (not Q8–Q27), including:  
   - factoid numerical questions,  
   - truncated-section neighbor needs (Q19-like),  
   - requirement/procedure phrasings.  
3. Evaluate ablations **as separate experiment planners** (still not production):  
   - G0 (current)  
   - G1: same classifier, but GENERAL incompleteness only on hits that pass a relevance/topic gate (not any truncated distractor)  
   - G2: optional expanded need keywords for factoids—but defined *before* looking at H2 answers  
4. Pre-register endpoints: skip rate, FP skip rate, GUARDED−HYBRID mean Δ, Q19-like neighbor-gap recovery.  
5. Keep Blind as a reference arm, not a production default.

Also keep Q19-style items as an explicit evaluation slice for selective vs blind neighbor choice.

---

## 16. Final Verdict

### Explicit answers

1. **Why skip 3/7 on development?**  
   Those questions matched specialized need classes (`procedure`, `requirement_evidence`) and specialized text checks found complete procedures/requirements in retrieved hits (Q2, Q6, Q7). **CONFIRMED.**

2. **Why skip 0/20 on held-out?**  
   19/20 fell to `general`; the GENERAL rule saw truncation/incompleteness signals in the top-5 every time and forced expand. Q24 used `duration_table` but also failed on truncated/incomplete table signals. **CONFIRMED.**

3. **Main problem: classification, sufficiency, or both?**  
   **Both.** Coverage failure routes questions to GENERAL; GENERAL sufficiency is overly truncation-triggered. **CONFIRMED.**

4. **Is the architecture fundamentally too restrictive?**  
   **LIKELY yes for GENERAL** (expand-unless-perfect). Specialized paths are narrow but not “fundamentally” impossible to improve. The *current frozen design* is too skip-restrictive off the Q1–Q7 phrasing distribution.

5. **Does Q19 show Blind can help certain questions?**  
   **Yes — CONFIRMED** for this truncated multi-chunk status list, stably across 5 seeds. Not a general endorsement of Blind.

6. **Single most logical next experiment?**  
   Ablation of GENERAL truncation logic + new held-out split H2 (Section 15)—not retuning on Q8–Q27.

7. **Additional independent evaluation data required?**  
   A third question split (H2) with more Q19-like neighbor gaps, more factoids, and more procedure/requirement phrasings; optional harder non-ceiling items; pre-registered FP-skip budget.

---

### Overall investigation verdict

**CONFIRMED: generalization failure is explained by narrow keyword classification plus an over-conservative GENERAL sufficiency rule—not by random seed noise or a broken experiment harness.**

No production or guard changes were made. Historical Step 8/9 artifacts untouched.

**Stop.** Awaiting review before any next phase.
