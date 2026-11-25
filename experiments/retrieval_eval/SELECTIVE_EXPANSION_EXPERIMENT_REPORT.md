# Phase 4.2 P1 Step 5 — Selective Neighbor Expansion A/B/C Experiment

**Verdict:** **PASS WITH ISSUES**  
**Mode:** Isolated experiment only (production RAG / neighbor expansion untouched)  
**Live run timestamp:** see `selective_expansion_results.json` → `meta.timestamp_utc`

---

## 1. Executive Summary

Five configurations were compared on Q1–Q7 with **identical** semantic hits, model (`llama3.2`), prompt, temperature (`0.2`), top_k (`5`), and min_similarity (`0.5`).

| Configuration | Mean answer total (/28) | Mean ctx chars | Mean neighbors | Mean “irrelevant” neighbors* |
|---|---:|---:|---:|---:|
| OFF | 21.0 | 4405 | 0.0 | 0.0 |
| BLIND (±1) | 21.6 | 7687 | 6.3 | 5.9 |
| **A_TABLE** | 21.9 | **4990** | **1.1** | **0.9** |
| **B_PROCEDURE** | 22.6 | 5488 | 2.1 | 2.0 |
| **C_EVIDENCE** | **25.0** | 5444 | 2.0 | 1.6 |

\*Experiment heuristic: neighbor not in primary/optional ground-truth set (same-doc non-primary counted).

**Highlights**

- **A_TABLE** fixed Q1 (methods + processing + 15:00) and kept Q2’s full 3-step procedure with **one** neighbor and low context — but **failed Q3** (did not pull `#5`) and **regressed Q6** badly.
- **B_PROCEDURE** pulled Q3’s 7-day rule and restored Q2 steps; still noisy extras; weak Q5 (missed category table).
- **C_EVIDENCE** best mean score: strong Q1/Q2/Q3 utilization with moderate context; Q5 improved vs OFF without BLIND’s bulk; residual noise/regressions remain.
- **BLIND** again showed large context and weak Q2/Q3 utilization relative to coverage.
- This run’s OFF/BLIND absolute scores **differ from Step 3** (24.0 / 22.4) due to LLM non-determinism; **do not overwrite** Step 3. Relative lessons still hold.

**Production recommendation:** **Not yet.** Prefer a **follow-up hybrid** (table-incomplete ∪ overdue/procedure-gap ∪ truncated-table next) with a hard neighbor cap, then re-score. C is the strongest *single* strategy in this run but heuristics are not production-ready alone.

---

## 2. Experimental Methodology

1. `SemanticSearchService.search` once per question (`top_k=5`, `min_similarity=0.5`).  
2. Apply experiment-only planners (OFF / BLIND / A / B / C).  
3. Load neighbor texts via read-only SQL.  
4. Format CONTEXT with production `build_context_blocks` / `format_context_blocks` when neighbors exist.  
5. Call Ollama `llama3.2` with production `rag_system_prompt` and `rag_temperature`.  
6. Human-score answers with the **Step 3 seven-metric 0–4 rubric** (unsupported_claims: higher = fewer unsupported claims).

Verified: `semantic_hits_identical_across_configs == true` for all questions.

---

## 3. Definitions of A / B / C

### Strategy A — Table-aware (`A_TABLE`)

| Item | Definition |
|---|---|
| Criteria | Retrieved text looks like a Markdown table (`|` density / header) **and** appears incomplete (truncated last cell, mid-word end, or header without enough data rows). |
| Direction | Prefer **next**; optional **previous** if continuation lacks header. |
| Max | 4 unique neighbors |
| Dedupe | Skip keys already in original hit set / already planned |
| Expected benefit | Q1 `#2`, Q5 `#1` table completion |
| Limitations | False positives on pipe-like text; may expand wrong tables (Q3/Q6) |

### Strategy B — Procedure-aware (`B_PROCEDURE`)

| Item | Definition |
|---|---|
| Criteria | Incomplete numbered steps; overdue section without “7 calendar days”; mid-procedure remnants. |
| Direction | **Next** and/or **previous** as needed |
| Max | 4 |
| Expected benefit | Q2/Q3 procedure completion |
| Limitations | Misses pure tables (Q5); can expand refund noise |

### Strategy C — Evidence-completion (`C_EVIDENCE`)

| Item | Definition |
|---|---|
| Criteria | Truncated chunk and/or overdue-definition gap; neighbor kept if lexically relevant **or** pipe-heavy table continuation **or** contains 7-calendar-day text. |
| Direction | Prefer **next**; previous only for lowercase remnants |
| Max | 4 + post-load relevance filter |
| Expected benefit | Q1 table + Q3 7-day with less blind noise |
| Limitations | Lexical gates can drop useful neighbors (fixed mid-experiment for tables); still expands some soft-irrelevant same-doc chunks |

### BLIND

Production-equivalent `plan_neighbors(window=1, max_expanded=10)` for both directions on every hit.

---

## 4. OFF vs BLIND vs A/B/C Results

### Context efficiency

| Config | Mean chars | Max chars | Mean blocks | Mean neighbors |
|---|---:|---:|---:|---:|
| OFF | 4405 | 4482 | 5.0 | 0 |
| BLIND | 7687 | 9457 | 11.0 | 6.3 |
| A_TABLE | 4990 | 5235 | 6.1 | 1.1 |
| B_PROCEDURE | 5488 | 6532 | 7.1 | 2.1 |
| C_EVIDENCE | 5444 | 6817 | 7.0 | 2.0 |

Selective strategies cut ~30–35% mean characters vs BLIND while retaining many useful attachments.

### Answer-quality totals (/28)

| Q | OFF | BLIND | A | B | C |
|---|---:|---:|---:|---:|---:|
| Q1 | 17 | 20 | **28** | 17 | 25 |
| Q2 | 21 | 17 | **28** | **28** | **28** |
| Q3 | 16 | 16 | 15 | 19 | **26** |
| Q4 | 26 | 26 | 26 | 26 | 26 |
| Q5 | 14 | 19 | 19 | 15 | **22** |
| Q6 | 26 | 26 | **10** | 26 | 21 |
| Q7 | 27 | 27 | 27 | 27 | 27 |
| **Mean** | 21.0 | 21.6 | 21.9 | 22.6 | **25.0** |

Detailed metric cells: `selective_expansion_scores.json`.

---

## 5. Q1–Q7 Answer-Quality Comparison

### Q1 — Does evidence-completion / table-aware help?
**Yes for A and C.**  
A alone produced methods **and** processing **and** 15:00. C produced methods + 15:00 (missed stating 1–2 processing). B did not attach `#2`. BLIND attached `#2` but still dropped processing (same pattern as Step 3/4).

### Q2 — Does procedure-aware improve?
**Yes (and A/C also).**  
A/B/C all emitted the full 3-step procedure. OFF/BLIND collapsed to one line despite `#5` in hits. Note: A’s selected neighbor was a **table** chunk (`#2`), not the procedure neighbor — the procedure was already in retrieved `#5`; smaller context likely helped utilization.

### Q3 — Does evidence-completion improve?
**Yes for C (and partially B).**  
C and B attached `delivery_policy.md#5` and **stated** the 7-calendar-day lost-package rule. A did **not** (expanded refund table `#4` instead). BLIND had `#5` in context but still failed to communicate it clearly in this run.

### Q5 — Does table-aware improve?
**Coverage yes; answer quality mixed.**  
A attached `#1` with **0** irrelevant neighbors and listed categories, but **invented** website “Contact Us” UI steps (unsupported_claims score 1). C also got `#1` and scored highest on Q5 this run without as much UI fabrication. B missed `#1`.

### Q4 / Q6 / Q7
- Q4 stable across all configs.  
- Q6: **A severe regression** (denied photo evidence was present). B/OFF/BLIND strong; C slightly messy.  
- Q7 stable/high for all.

---

## 6. Context-Efficiency Comparison

**Least context among expanding strategies:** A_TABLE (~4990 chars, ~1.1 neighbors).  
**Best quality per mean char:** C (25.0 at ~5444) beats BLIND (21.6 at ~7687).  
**OFF** remains smallest but loses Q1 `#2`, Q3 `#5`, Q5 `#1` coverage.

---

## 7. Irrelevant-Neighbor Analysis

| Config | Typical noise |
|---|---|
| BLIND | Handbook/refund/privacy/product neighbors on many queries |
| A | Occasional wrong-table expansions (Q3 refund `#4`, Q4 support, Q6 product) |
| B | Refund procedure neighbors + handbook on Q1/Q5 |
| C | Truncation-triggered extras (privacy/refund) even after relevance filter |

A introduced the **least** average irrelevant neighbors among expanding configs.

---

## 8. Regressions and Improvements

| Change | Improvement | Regression |
|---|---|---|
| A vs BLIND | Q1, Q2 quality; much less context | Q3 still weak; **Q6 collapse** |
| B vs BLIND | Q2, Q3 (partial); less context | Q5 misses categories; Q1 no table |
| C vs BLIND | Q1, Q2, Q3 strong; Q5 better mean | Some Q6 softness; not zero noise |
| A vs B vs C | A best efficiency + perfect Q1; C best overall mean + Q3 | No single strategy wins all questions |

---

## 9. Limitations

1. **n=1 generation per cell** — LLM variance is large (this OFF mean 21.0 vs Step 3’s 24.0).  
2. Heuristic false positives/negatives (A on Q6; B on Q5; early C table drop fixed mid-step).  
3. “Irrelevant neighbor” metric is ground-truth-proxied, not human topical judgment.  
4. No multi-seed / multi-temperature replication.  
5. Does not test prompt changes or re-chunking.  
6. Historical Step 3/4 reports **not** overwritten; numbers are not directly pooled.

---

## 10. Recommended Production Strategy

**Insufficient evidence for immediate production swap to a single heuristic.**

**If forced to pick one experimental direction to productize next:** start from **C_EVIDENCE** (best mean, fixes Q3 communication in this run, moderate context) **merged with A’s strict incomplete-table → next-only rule** and a **hard cap (e.g. 3)**, then:

1. Re-run this harness ≥3 seeds.  
2. Gate on Q1–Q7 means **and** no Q6-style regressions.  
3. Only then patch production `neighbor_expansion` behind a flag.

**Do not** ship A alone (Q6 risk) or BLIND as quality default.

---

## 11. Final Verdict

### **PASS WITH ISSUES**

The isolated A/B/C experiment completed successfully with controlled retrieval, live answers, rubric scores, and efficiency metrics. Selective expansion **can** beat blind ±1 on both quality and context size (especially **C**, with **A** excelling on Q1 efficiency), but heuristics remain brittle and **not** production-approved without a hybrid + replication pass.

### Files created (experiment only)

| File | Role |
|---|---|
| `experiments/retrieval_eval/selective_strategies.py` | A/B/C/OFF/BLIND planners |
| `experiments/retrieval_eval/run_selective_experiment.py` | Isolated live harness |
| `experiments/retrieval_eval/selective_expansion_results.json` | Raw answers / context stats |
| `experiments/retrieval_eval/selective_expansion_scores.json` | Human rubric scores |
| `experiments/retrieval_eval/SELECTIVE_EXPANSION_EXPERIMENT_REPORT.md` | This report |

### Unchanged confirmation

Production code, prompts, configuration defaults, semantic search, production neighbor expansion, chunking, database records, embeddings, Q1–Q7 ground truth, Step 3/4 reports, and retrieval baselines were **not** modified.

**Stop.** Awaiting approval before any production implementation.