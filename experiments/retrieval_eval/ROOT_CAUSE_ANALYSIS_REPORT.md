# Phase 4.2 P1 Step 4 — RAG Answer Quality Root Cause Analysis

**Task type:** Investigation only (no implementation)  
**Verdict:** **PASS WITH ISSUES**  
**Evidence sources:** Step 2C live OFF/ON capture (`/tmp/rag_neighbor_live_validation.json`, timestamp `2026-11-24T06:17:46Z`), Step 3 answer rubric (`ANSWER_LEVEL_EVALUATION_REPORT.md`, `answer_level_eval_scores.json`), `dataset.py`, `neighbor_expansion.py`, `rag.py`, `config.py` `rag_system_prompt`.

This report distinguishes **observed facts** from **hypotheses**. Prior Step 3 hypotheses are re-tested against block-level evidence and are not treated as proven by default.

---

## 1. Executive Summary

Neighbor expansion correctly attaches missing adjacent chunks and improves CONTEXT coverage, but mean answer quality fell from **24.0/28 (OFF)** to **22.4/28 (ON)**.

| Pattern | Observed |
|---|---|
| Q1 (−6) | Processing time and 15:00 cutoff **were present** in ON CONTEXT inside retrieved `delivery_policy.md#1`; the model answered mainly from the newly completed transit table (`#2`) and omitted those facts. |
| Q2 (−7) | Full three-step lost-package procedure remained in retrieved `#5`; ON moved `#5` later in a **~2× larger** CONTEXT with many neighbors; the answer collapsed to a one-line summary. |
| Q3 (+1 coverage, weak utilization) | Explicit “7 calendar days” sentence was in ON CONTEXT as `neighbor_next` from `#4` (block **[9]/14**); the answer discussed overdue definition and support process but **did not state that rule**. |
| Q5 (+7) | `customer_support_guidelines.md#1` attached immediately after `#0` and **completed a truncated category table**; the model copied that structured list into the answer. |

**Most likely root-cause class for quality regressions:** **model synthesis + prompt trade-offs under expanded multi-block CONTEXT**, not missing retrieval of the omitted facts (except historically under OFF for Q1 `#2` / Q3 `#5` / Q5 `#1`). Ranking was identical OFF vs ON.

---

## 2. Q1 Root Cause Analysis — Delivery Duration

### 2.1 What was omitted in ON

ON answer covered Standard / Expedited / Overnight transit only. It omitted:

- In-stock processing **1–2 business days**
- Orders after **15:00** processed next business day  
(both present in OFF answer)

### 2.2 Were those facts in final LLM CONTEXT?

**Yes (observed).**  
ON block **[4]** `role=retrieved` `delivery_policy.md#1` preview begins with Processing Times and “1–2 business days”. The same chunk also contains the 15:00 rule in the stored full text (verified in prior DB audits; Step 2C phrase flags show processing content retained in CONTEXT).

Complete shipping methods (Expedited, Overnight, Freight) appear in ON block **[5]** `role=neighbor_next` `delivery_policy.md#2` (expanded from `#1`).

### 2.3 Block completeness and position

| Mode | `#1` (processing / 15:00 / truncated table) | `#2` (full table) |
|---|---|---|
| OFF | Retrieved block **[3]** of 5 | **Absent** |
| ON | Retrieved block **[4]** of 7 | Neighbor block **[5]** immediately after `#1` |

ON also inserts `neighbor_previous` `#3` after retrieved `#4` (status/overdue adjacency), pushing `#1` one slot later than OFF.

Duplicate/overlap: `#1` still ends mid-row (“Defaul…”); `#2` continues the table with overlap strip (`text_len=400`). Competing early blocks include signature policy `#6` and overdue definitions `#4` — same ranked hits as OFF.

### 2.4 Prompt pressure (observed wording)

Production prompt includes both:

- “**Be concise** and accurate.”
- “**summarize** relevant timelines, numbers, conditions, and procedures”
- “**Use only portions** of CONTEXT that are relevant… **ignore** unrelated…”

There is **no** instruction requiring the answer to enumerate *all* timeline types (processing vs transit) when both appear.

### 2.5 Origin classification (Q1)

| Layer | Role in Q1 ON regression |
|---|---|
| Retrieval ranking | Unchanged; not the ON omission cause |
| Context preparation | **Helped** by adding `#2`; did **not** remove processing text |
| Prompt | **Partially contributes** via concise/summarize/ignore guidance |
| Model synthesis | **Primary observed failure mode**: selected transit-table facts; dropped co-present processing facts |

**Fact:** Omission is not due to absent processing evidence under ON.  
**Hypothesis:** Newly completed table dominates attention; “concise” encourages a shorter transit-only answer.

---

## 3. Q2 Root Cause Analysis — Overdue Package

### 3.1 OFF procedure steps available

OFF retrieved `#5` (block **[3]**/5) contains:

1. Verify carrier tracking  
2. Contact carrier within one business day  
3. Offer replacement/refund if confirmed lost after **7 calendar days**

OFF answer reproduced all three steps.

### 3.2 What changed ON

- Same original top-5 sources/scores as OFF.  
- `#5` still retrieved, but as block **[6]** of **13** (after neighbors `#3`, `#0`, `#2`).  
- Context chars **4449 → 8901**; neighbors **0 → 8**.  
- Added same-doc delivery neighbors plus handbook `#4/#6` and refund `#0/#2` (PTO, VPN/patches already in handbook `#5`, photo windows, status tables).

ON answer: *“If a package is overdue by 7 calendar days, support agents must offer a replacement or refund.”*  
Lost steps 1–2; compressed condition (“overdue by 7 days” vs “confirmed lost after 7 calendar days”).

### 3.3 Most likely root cause (evidence-based)

| Candidate | Assessment |
|---|---|
| Evidence deleted from CONTEXT | **Not supported** — `#5` still present with full step list in preview |
| Unrelated neighbors introduced | **Confirmed** — handbook/refund neighbors added (some topics already in OFF hits) |
| Important evidence later in CONTEXT | **Confirmed position shift** — `#5` from early [3] to mid [6] in a much longer prompt |
| Model summarized instead of preserving procedure | **Confirmed by answer text** |
| Dilution as sole proven cause | **Not proven** — correlated with size/noise/order; needs controlled ablation |

**Most likely:** **model summarization under larger, noisier CONTEXT**, amplified by prompt “Be concise” / “summarize”, with **partial support** from later placement of `#5` and unrelated neighbors.

---

## 4. Q3 Evidence Utilization — Late Delivery Refund

### 4.1 Exact evidence wording (ON)

Neighbor block **[9]** `delivery_policy.md#5` (`expanded_from_chunk_index=4`):

> … Offer a replacement or refund if the package is confirmed lost after **7 calendar days**. …

Phrase flag: `7 calendar days` **True** in ON CONTEXT, **False** in OFF CONTEXT.

### 4.2 Position and competition

ON CONTEXT has **14** blocks (~9457 chars). Order highlights:

1. **[1]** `refund_policy.md#1` — eligibility windows + **photographic evidence** (distractor for late delivery)  
2. Multiple refund neighbors  
3. **[7]** `delivery_policy.md#4` — overdue definition  
4. **[9]** `delivery_policy.md#5` — **7-day rule**  
5. **[10]** `refund_policy.md#3` — overdue **Conditional**  
6. **[12]** support guidelines checklist (“check order status… apply Refund Policy…”)

### 4.3 Prompt support for multi-chunk evidence

Prompt **does** say not to abstain merely because evidence is split across bullets/rows and to keep eligibility conditions separate. It also says be concise, summarize, and ignore unrelated portions.

### 4.4 Why availability ≠ answer

**Observed answer behavior:**

- Restates overdue definition (from `#4`).  
- Emphasizes refund is **not automatic**.  
- Echoes **support-process** checklist language (aligned with guidelines `#5`).  
- Never quotes the lost-after-7-calendar-days rule.

**Interpretation:**

- Model treated the question as “is refund automatic?” and answered cautiously.  
- It underweighted the delivery overdue **procedure** neighbor relative to front-loaded refund + support process blocks.  
- Possible confusion between “late delivery” (customer phrasing) and “confirmed lost after 7 calendar days” (policy phrasing) — **hypothesis**, consistent with answer avoiding that sentence.

**Origin:** Not missing expansion; **evidence utilization / synthesis failure** in a crowded CONTEXT. Prompt partially encourages separation of rules but does not require citing the strongest matching condition when present.

---

## 5. Q5 Positive Improvement — Customer Support

### 5.1 What neighbors contributed

ON block **[2]** `neighbor_next` `customer_support_guidelines.md#1` expanded from `#0`:

- Completes Ticket Categories table rows (`billing`, `shipping`, `product_defect`, `refund_request`, …).

OFF lacked `#1`; `#0` only starts the table.

### 5.2 Why the answer improved

**Observed:** ON answer lists categories and reproduces the table structure from CONTEXT. Rubric +7.

**Difference vs Q1/Q2/Q3:**

| Factor | Q5 (success) | Q1/Q2/Q3 (problems) |
|---|---|---|
| Missing piece type | Single truncated **table continuation** | Multi-aspect timelines / multi-step procedure / conditional rule amid distractors |
| Neighbor placement | Immediately after seed hit (**[1]→[2]**) | Useful facts mid-pack among many neighbors (Q2/Q3) or competing with new salient table (Q1) |
| Answer shape | Extractive list/table copy | Requires synthesis across fact types |
| Extra neighbors | Also present (refund/privacy) | Similar noise, but Q5’s critical completion is early and highly structured |

**Fact:** Improvement came from **context completeness of a structured artifact**, not from ranking changes.

---

## 6. Cross-Question Comparison

| Q | Coverage OFF→ON | Answer quality Δ | Dominant mechanism |
|---|---|---|---|
| Q1 | `#2` added | −6 | Synthesis prefers new table; drops co-present processing |
| Q2 | Already covered | −7 | Summarization under ~2× context |
| Q3 | `#5` added | +1 weak | Underuse of explicit neighbor evidence |
| Q4 | Stable | 0 | Simple fact; noise ignored in answer |
| Q5 | `#1` added | +7 | Extractive use of completed table |
| Q6 | Stable | −2 | Mild digression from neighbors |
| Q7 | Stable | −4 | Eligibility dump mixed into process answer |

---

## 7. Context Dilution Investigation

**Observed correlations:**

- Larger CONTEXT ↔ lower scores on Q1/Q2/Q7.  
- Q5 also larger CONTEXT but higher score.  
- Therefore **size alone does not determine quality**.

**Observed mechanisms that look like dilution:**

1. More competing topical blocks (Q2 handbook/refund; Q3 photo + support process).  
2. Critical procedure block placed later (Q2 `#5`).  
3. Prompt “ignore unrelated” + “concise” may license dropping details.

**Not proven:** that character count causally reduces quality without the content/order/prompt factors.

---

## 8. Root Causes versus Hypotheses

| # | Hypothesis | Classification | Evidence |
|---|---|---|---|
| 1 | Larger context causes evidence dilution | **Partially supported** | Correlated on Q1/Q2/Q7; contradicted by Q5 |
| 2 | Context block ordering affects attention | **Partially supported** | Q2 `#5` later ON; Q5 useful neighbor early; needs order-ablation test |
| 3 | Duplicate overlapping chunks reduce quality | **Partially supported** | Overlap exists OFF too; ON strips many next-neighbor prefixes; not sufficient alone |
| 4 | Expansion introduces unrelated content | **Confirmed** (presence) | Handbook/refund/privacy neighbors ON; **not confirmed** as sole answer-failure cause |
| 5 | Llama 3.2 struggles with distributed evidence | **Partially supported** | Q3 fails despite explicit sentence; Q5 succeeds on contiguous table completion; needs model A/B |
| 6 | Prompt insufficiently prioritizes completeness | **Partially supported** | “Be concise” / “summarize” / “ignore unrelated” observed; no “list all matching timeline types” rule |
| 7 | Selective expansion could improve context→answer | **Requires further testing** | Strong rationale from Q5 vs Q2/Q3 patterns; not yet measured |

### Confirmed root causes (narrow)

1. **Blind ±1 expansion increases CONTEXT volume and topical adjacency noise** (implementation behavior).  
2. **Answer regressions under ON are primarily generation/utilization failures**, not deletion of the omitted facts from CONTEXT (Q1 processing, Q2 steps, Q3 7-day text).  
3. **Q5 gain is explained by completing a truncated structured table via the immediate next neighbor.**

---

## 9. Improvement Options and Trade-offs

*Analysis only — not implemented.*

| Option | Expected benefit | Risks | Complexity | How to measure |
|---|---|---|---|---|
| **A. Selective neighbor expansion** | Keep Q5-style wins; cut Q2/Q3 noise | Miss useful neighbors if heuristics wrong | Medium | Repeat Step 3 rubric OFF / ON-blind / ON-selective |
| **B. Expand only table/procedure-like chunks** | Targets Q1/Q3/Q5 failure modes | Heuristic errors; miss prose-only gaps | Medium | Coverage of primary chunks + answer totals |
| **C. Lower `rag_max_expanded_neighbors`** | Smaller prompts (e.g. cap 2–4) | May drop useful second-priority neighbors | Low | Context size + rubric; watch Q5 still gets `#1` |
| **D. Improve context ordering** | Put neighbors beside seed; rank by usefulness | Reorder bugs; still noisy if too many | Medium | Ablate order holding chunk set fixed |
| **E. Stronger overlap dedupe** | Less repeated text | Over-stripping unique boundaries | Low–medium | Overlap metrics + rubric |
| **F. Section/table-aware chunking** | Fewer split tables/procedures | Re-ingest/re-embed cost | High | Retrieval Recall@K + answer rubric |
| **G. Completeness-oriented prompt tweak** | Force processing+transit; full procedures | Longer answers; more noise echoed | Low | Same OFF/ON sets; hallucination checks |
| **H. Different model / temperature comparison** | Isolate model synthesis limits | Cost; not a retrieval fix | Low–medium | Identical CONTEXT replay across models |

Do **not** pick a single option as proven best without a controlled follow-up experiment.

---

## 10. Recommended Next Experiment

**Primary recommendation:** a **controlled selective-expansion A/B/C** (still evaluation-first):

1. **A:** expansion OFF  
2. **B:** current blind ±1 (max 10)  
3. **C:** selective rule — e.g. expand next neighbor only when retrieved chunk appears truncated (mid-word / broken table row) **or** ends inside a numbered procedure; cap total expanded neighbors at **3**

Hold model, prompt, top_k, threshold, embeddings fixed. Score with the **existing Step 3 answer rubric** plus primary-chunk CONTEXT coverage.

**Secondary (optional parallel):** replay the **same frozen ON CONTEXT** for Q1/Q2/Q3 through an alternate model or temperature to classify hypothesis 5 vs 6 — without changing production defaults.

Do not implement until approved.

---

## 11. Final Verdict

### **PASS WITH ISSUES**

The investigation is complete and evidence-backed. Neighbor expansion’s coverage gains are real; answer-quality regressions are best explained by **how `llama3.2` synthesizes long, multi-topic CONTEXT under a concise/summarize prompt**, not by failure to attach or retain the omitted facts in CONTEXT for Q1/Q2/Q3 ON. Q5 shows expansion **can** improve answers when it completes a truncated structured artifact early in CONTEXT.

### Protected systems confirmation

| Area | Status |
|---|---|
| Production code | Unchanged |
| Prompts / config defaults | Unchanged |
| Neighbor expansion / search / chunking | Unchanged |
| Database / embeddings | Unchanged |
| Q1–Q7 ground truth | Unchanged |
| Retrieval baseline JSON | Not overwritten |
| New artifact | This report only |

### File created

- `experiments/retrieval_eval/ROOT_CAUSE_ANALYSIS_REPORT.md`

**Stop.** Awaiting approval before any implementation.