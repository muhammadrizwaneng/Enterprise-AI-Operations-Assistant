# Phase 4.2 P1 Step 3 — Answer-Level Evaluation Report

**Task type:** Investigation / evaluation only (no implementation)  
**Verdict:** **PASS WITH ISSUES**  
**Evaluation timestamp (source run):** `2026-11-24T06:17:46Z` (UTC)  
**Scoring method:** Human rubric applied to captured live OFF/ON RAG answers (not LLM-as-judge)

---

## 1. Executive Summary

Neighbor expansion reliably improves **context coverage** for several Q1–Q7 gaps (notably Q1 table chunk `#2`, Q3 seven-day chunk `#5`, Q5 ticket-category chunk `#1`). It does **not** reliably improve **generated answer quality**.

Human rubric totals (sum of seven 0–4 metrics; max 28):

| Mode | Mean total | Mean completeness | Mean evidence utilization |
|---|---:|---:|---:|
| Expansion **OFF** | **24.0** | 2.86 | 3.43 |
| Expansion **ON** | **22.4** | 2.71 | 2.71 |

Per-question total deltas (ON − OFF): Q5 **+7**, Q3 **+1**, Q4 **0**, Q6 **−2**, Q7 **−4**, Q1 **−6**, Q2 **−7**.

**Bottom line:** Expanding every retrieved hit increases average context from ~4.4k to ~7.7k characters and fills missing primary chunks, but the current `llama3.2` + prompt stack often underuses new evidence (Q3) or drops previously stated facts (Q1, Q2). Selective expansion and/or answer-focused evaluation gates are warranted before treating expansion-ON as an unqualified quality win.

---

## 2. Evaluation Methodology

### 2.1 Infrastructure inspected

| Asset | Role |
|---|---|
| `experiments/retrieval_eval/dataset.py` | Q1–Q7 questions + primary/optional chunk ground truth |
| `experiments/retrieval_eval/metrics.py` / `run_eval.py` | Retrieval metrics (Recall@K, MRR, etc.) — **not** answer quality |
| `/tmp/retrieval_eval_baseline.json` | Retrieval baseline — **not overwritten** |
| `/tmp/rag_neighbor_live_validation.json` | Step 2C live OFF/ON capture (answers, sources, context blocks, sizes) |
| `backend/app/services/rag.py` + `neighbor_expansion.py` | How CONTEXT is assembled; sources = original ranked hits only |

### 2.2 Controlled comparison design

| Held constant | Value |
|---|---|
| Questions | Exact Q1–Q7 strings from `dataset.py` |
| Model | `llama3.2` via Ollama |
| System prompt | Production `rag_system_prompt` |
| Temperature | `0.2` |
| Top-K | `5` |
| Min similarity | `0.5` |
| Embeddings / DB | Unchanged 46 chunks / 6 docs |
| Only changed | `rag_neighbor_expansion_enabled` False vs True (runtime Settings override; not persisted) |

Window / max neighbors when ON: `rag_neighbor_window=1`, `rag_max_expanded_neighbors=10`.

### 2.3 Data used for scoring

This Step 3 report **reuses** the Step 2C live capture rather than regenerating answers (same controlled settings; avoids extra non-determinism). Supporting score artifact:

- `experiments/retrieval_eval/answer_level_eval_scores.json`
- Mirror: `/tmp/answer_level_eval_scores.json`

Original retrieval baseline JSON was not modified.

### 2.4 What was *not* used as sole judge

Scores are **human** judgments against the rubric below, grounded in:

1. Exact answer text  
2. Whether required facts appear in the prepared CONTEXT  
3. Document policy wording from retrieved/expanded chunks  
4. Source attribution lists  

No automated LLM judge was used as the scoring authority.

---

## 3. Scoring Rubric (0–4)

Higher is always better. For **unsupported claims**, a higher score means **fewer** unsupported claims.

### 3.1 Correctness

| Score | Meaning |
|---|---|
| 0 | Mostly wrong or contradicts documented policy |
| 1 | Mix of wrong and right; major factual errors |
| 2 | Partially correct; important inaccuracies remain |
| 3 | Mostly correct; minor imprecision |
| 4 | Accurate relative to supplied CONTEXT / policy text |

### 3.2 Completeness

| Score | Meaning |
|---|---|
| 0 | Fails to answer the question |
| 1 | Mentions topic but omits most required facts |
| 2 | Some required facts; major gaps |
| 3 | Most required facts; minor omissions |
| 4 | Covers the expected primary facts for the question |

### 3.3 Evidence utilization

| Score | Meaning |
|---|---|
| 0 | Ignores available relevant CONTEXT |
| 1 | Uses little of the available relevant evidence |
| 2 | Uses some evidence; misses critical available facts |
| 3 | Uses most available relevant evidence |
| 4 | Clearly uses the key available evidence (including expanded neighbors when present) |

### 3.4 Unsupported claims *(higher = fewer unsupported claims)*

| Score | Meaning |
|---|---|
| 0 | Severe fabrication (e.g. invented phone/email/policy) |
| 1 | Multiple material unsupported claims |
| 2 | At least one material unsupported claim |
| 3 | Only minor overreach / soft speculation |
| 4 | No material unsupported claims |

### 3.5 Preservation of important conditions and exceptions

| Score | Meaning |
|---|---|
| 0 | Merges or invents conditions dangerously |
| 1 | Drops or conflates major conditions |
| 2 | Partial preservation; important condition missing |
| 3 | Most conditions preserved |
| 4 | Conditions/exceptions stated accurately |

### 3.6 Relevance

| Score | Meaning |
|---|---|
| 0 | Off-topic |
| 1 | Mostly off-topic |
| 2 | Mixed relevant / digression |
| 3 | Mostly on-topic with minor extras |
| 4 | Tightly answers the asked question |

### 3.7 Source consistency

| Score | Meaning |
|---|---|
| 0 | Answer conflicts with attributed sources / invents provenance |
| 1 | Weak alignment |
| 2 | Partial alignment |
| 3 | Good alignment; minor tension |
| 4 | Answer consistent with attributed original sources; neighbors not misrepresented as ranked hits |

Each scored cell in this report includes a short rationale. Full structured scores live in `answer_level_eval_scores.json`.

---

## 4. OFF vs ON Results for Q1–Q7

### 4.1 Aggregate metrics

| Metric (mean / 4) | OFF | ON | Δ |
|---|---:|---:|---:|
| Correctness | 3.57 | 3.29 | −0.29 |
| Completeness | 2.86 | 2.71 | −0.14 |
| Evidence utilization | 3.43 | 2.71 | −0.71 |
| Unsupported claims (↑ better) | 3.71 | 3.57 | −0.14 |
| Conditions / exceptions | 3.00 | 2.71 | −0.29 |
| Relevance | 3.86 | 3.57 | −0.29 |
| Source consistency | 3.57 | 3.86 | +0.29 |
| **Mean total / 28** | **24.0** | **22.4** | **−1.6** |

### 4.2 Per-question totals

| Q | OFF total | ON total | Δ | Primary coverage change |
|---|---:|---:|---:|---|
| Q1 | 26 | 20 | −6 | `#2` missing → present |
| Q2 | 27 | 20 | −7 | already complete both |
| Q3 | 16 | 17 | +1 | `#5` missing → present |
| Q4 | 26 | 26 | 0 | already complete |
| Q5 | 20 | 27 | +7 | `#1` missing → present |
| Q6 | 26 | 24 | −2 | already complete |
| Q7 | 27 | 23 | −4 | already complete |

### 4.3 Context size (from Step 2C capture)

| | OFF | ON |
|---|---:|---:|
| Mean context chars | ~4405 | ~7687 |
| Mean blocks | 5 | 11 |
| Mean neighbors | 0 | 6 |
| Max context chars | 4482 | 9457 (Q3) |

**Retrieval ranking:** original source lists and similarities were **identical** OFF vs ON for every question.

---

## 5. Individual Question Analysis

### Q1 — Delivery duration

**Expected primary facts:** processing 1–2 business days; orders after 15:00 process next business day; Standard Ground 3–7 business days; distinguish processing vs transit; do not invent a single guaranteed total.

**OFF answer (score total 26):** Included processing, 15:00, and Standard Ground 3–7. Completeness limited by missing full methods table (`#2` not in context), but truncated `#1` already contained Standard Ground.

**ON answer (score total 20):** Neighbor `#2` present (`role=neighbor_next`). Answer listed Standard / Expedited / Overnight, but **omitted** processing and 15:00 even though retrieved `#1` remained in CONTEXT. Overnight phrased as “1 business day” vs document “Next business day” (minor drift).

**Why omissions happen (observed + hypothesis):**  
- **Observed:** Relevant processing/15:00 text was still in CONTEXT under ON; omission is not due to missing retrieval of those facts.  
- **Hypothesis:** Model attention shifted to the newly completed transit table; prompt does not force enumeration of all timeline *types* (processing vs transit). Context growth is correlated, not proven causal by itself.

### Q2 — Overdue package / seven days

**Expected:** verify tracking; contact carrier within one business day; offer replacement/refund if confirmed lost after **7 calendar days**.

**OFF (27):** Full three-step procedure.  
**ON (20):** Shortened to “offer a replacement or refund” after 7 calendar days — **lost verify + contact steps**.

**Why shorter with more context:**  
- **Observed:** Primary `#4`/`#5` present in both modes; ON added ~8 neighbors and ~2× characters, including handbook/refund distractors already partially present OFF.  
- **Hypothesis:** Larger / noisier CONTEXT encourages summarization that drops procedural preconditions (context dilution **candidate**, not proven sole cause).

### Q3 — Late delivery refund

**Expected:** keep overdue Conditional vs defective-photo rules separate; include lost-after-7-calendar-days replacement/refund path when available; no automatic refund promise.

**OFF (16):** `#5` absent from context; vague eligibility; avoided photo-for-late invention.  
**ON (17):** `#5` **present** with explicit 7-calendar-day sentence as supporting neighbor; answer still did **not** clearly state that rule — emphasized “not automatic” and generic support process.

**Is evidence explicit in prepared context?** **Yes** (observed): neighbor block for `delivery_policy.md#5` includes *“Offer a replacement or refund if the package is confirmed lost after **7 calendar days**.”*  
**Root issue for answer gap:** evidence utilization / generation behavior, **not** missing expansion.

### Q4 — PTO notice period

Both modes score **26**: correct “at least 7 days … when possible.” VPN/OS patch text appears in CONTEXT (co-located in handbook `#5`) but **not** in answers. Expansion did not introduce answer-level confusion here.

### Q5 — Customer support contact

**OFF (20):** Ticket path only; incomplete categories (`#1` missing).  
**ON (27):** Full category table via neighbor `#1` — clearest **answer-quality win**.

**Why improvement:** The missing primary chunk is exactly the category table continuation; expansion attaches it to retrieved `#0`, and the model used that concrete table content.

### Q6 — Defective evidence

Both remain strong; ON slightly lower (26→24) due to broader restocking digression from neighbors — still grounded, slightly less tight relevance.

### Q7 — Refund process

OFF strong process answer (27). ON (23) still correct on `refund_request` / RMA but **mixes eligibility windows, photo evidence, restocking** into a “process” answer — more complete policy dump, less focused process narrative.

---

## 6. Context-Size and Context-Dilution Analysis

### Observed (verified)

1. Mean CONTEXT size ↑ ~75% with expansion ON.  
2. Original ranked sources unchanged.  
3. Q1/Q2 answer completeness ↓ while size ↑.  
4. Q5 completeness ↑ while size ↑.  
5. Adjacent retrieved chunks OFF already contain ~100-character overlap duplication; ON strips many **next**-neighbor prefixes (often `text_len≈400`).  
6. Same-document neighbors can introduce topical adjacencies (handbook equipment/VPN near PTO; product docs near refund evidence).

### Not proven

- That larger context **causes** omissions (could be model sampling / summarization preference).  
- That every extra neighbor is harmful.  
- That dilution is the only mechanism (Q3 failure is underuse of an explicit in-context sentence).

### Working hypothesis (labeled)

**Selective attention / summarization under longer multi-block CONTEXT** reduces procedural completeness for some queries, while structured tables (Q5 categories, Q1 methods) are easier for the model to latch onto — producing mixed outcomes.

---

## 7. Unsupported Claims and Omissions

### Unsupported / imprecise claims

| Mode | Finding | Severity |
|---|---|---|
| ON Q1 | Overnight as “1 business day” vs “Next business day” | Minor |
| ON Q2 | “Must offer” without stating verify/contact steps | Mild oversimplification |
| Both | No invented phone/email/URL observed on Q5 | Good |
| Both | No automatic full refund promise on Q3 | Good |

### Important omissions

| Mode | Omission |
|---|---|
| OFF Q1 | Full shipping methods beyond truncated Standard Ground |
| ON Q1 | Processing 1–2 days; 15:00 cutoff |
| ON Q2 | Verify tracking; contact carrier within one business day |
| OFF Q3 | Seven-calendar-day lost-package rule (chunk absent) |
| ON Q3 | Same rule **still omitted from answer** though present in CONTEXT |
| OFF Q5 | Full ticket category list |

---

## 8. Selective Neighbor Expansion Investigation (Analysis Only)

Expanding **every** top-5 hit (±1) is not always necessary.

| Strategy | Relevance to findings | Risk | Complexity |
|---|---|---|---|
| Expand only near Markdown tables | Helps Q1 `#1→#2`, Q5 `#0→#1` | Need table detection heuristics | Medium |
| Expand only near numbered procedures | Helps Q3 `#4→#5` | May miss tables | Medium |
| Expand when retrieved text looks truncated (ends mid-row / mid-sentence) | Directly targets `#1` “Defaul…” truncation | Heuristic false positives | Low–medium |
| Limit expansion per hit / global cap lower than 10 | Would shrink Q2/Q3/Q6 context bloat | May miss useful neighbors if many hits | Low |
| Section-aware boundaries | Best long-term structural fix | Requires re-chunk / re-embed | High |

**Analysis conclusion:** Blind ±1 on all hits maximizes recall of adjacent evidence but maximizes dilution. A **truncated-chunk or structure-triggered** expansion policy is the most justified next experiment — **not implemented in this task**.

---

## 9. Overall Comparison

| Dimension | Winner | Notes |
|---|---|---|
| Retrieval ranking quality | Tie | Identical by design |
| Primary chunk coverage in CONTEXT | **ON** | Fixes Q1 `#2`, Q3 `#5`, Q5 `#1` |
| Mean answer rubric total | **OFF** | 24.0 vs 22.4 |
| Best single-question gain | **ON Q5** | +7 |
| Worst single-question regressions | **ON Q1/Q2** | −6 / −7 |
| Hallucination control | Tie / slight OFF | Both generally safe |
| Context efficiency | **OFF** | Less noise, smaller prompt |

Neighbor expansion is a **context-assembly success** and an **answer-quality mixed result**.

---

## 10. Root Causes vs Hypotheses

| Item | Status |
|---|---|
| Expansion does not change semantic ranking | **Root cause / design** (confirmed) |
| Missing Q1 `#2` / Q3 `#5` / Q5 `#1` under OFF top-5 | **Root cause**: ranking + character chunk splits (prior P1 audit) |
| Expansion attaches those neighbors when adjacent hit retrieved | **Confirmed** |
| Q3 answer omits 7-day rule despite in-context evidence | **Confirmed generation/utilization gap**; not missing context under ON |
| Q1 ON drops processing/15:00 | **Confirmed omission**; causal link to dilution = **hypothesis** |
| Q2 ON shortens procedure as context grows | **Confirmed outcome**; dilution = **hypothesis** |
| Q5 improves because neighbor supplies category table | **Confirmed** |
| Re-chunking would reduce need for blind expansion | **Hypothesis** (strong, prior evidence) |

---

## 11. Recommended Next Steps

*(For review/approval — not started here.)*

1. **Keep retrieval eval + answer rubric separate**; add a repeatable answer-level harness that scores captured answers against this rubric (human or checklist), without changing ground-truth chunk IDs.  
2. **Prototype selective expansion** (truncated detection / table|procedure triggers; lower max neighbors) and re-run this same OFF/ON/selective answer rubric.  
3. **Consider prompt micro-guidance** only after selective expansion: e.g. require stating processing vs transit when both appear — separate approval.  
4. **Plan table/procedure-aware re-chunking** so critical rows are not neighbor-dependent.  
5. Do **not** treat expansion-ON as default quality upgrade based on context coverage alone.

---

## Verdict

### **PASS WITH ISSUES**

**Evidence:** Controlled OFF/ON live answers were scored with an explicit human rubric. Expansion ON improves context coverage and Q5 answer quality, but mean answer scores decline, with clear regressions on Q1 and Q2 and persistent underuse of Q3’s newly available seven-day evidence. No production systems were changed for this investigation.

---

## Files Created or Modified

| Path | Action |
|---|---|
| `experiments/retrieval_eval/ANSWER_LEVEL_EVALUATION_REPORT.md` | **Created** (this report) |
| `experiments/retrieval_eval/answer_level_eval_scores.json` | **Created** (supporting scores; separate from retrieval baseline) |
| `/tmp/answer_level_eval_scores.json` | **Created** (mirror) |

**Not modified:** production code, prompts, configuration defaults, semantic search, neighbor expansion implementation, chunking, database/embeddings, `dataset.py` ground truth, `/tmp/retrieval_eval_baseline.json`.

---

## Unchanged Confirmation

| Area | Status |
|---|---|
| Production application code | Unchanged |
| RAG prompts | Unchanged |
| Persistent configuration / `.env` | Unchanged |
| Database records / embeddings | Unchanged (Step 2C fingerprint check; this step read-only) |
| Q1–Q7 dataset / ground truth | Unchanged |
| Retrieval evaluation baseline JSON | Unchanged / not overwritten |

**Stop.** Awaiting review and approval before any implementation.