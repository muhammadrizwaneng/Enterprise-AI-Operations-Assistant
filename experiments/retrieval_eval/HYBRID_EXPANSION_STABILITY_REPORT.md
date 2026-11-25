# Phase 4.2 P1 Step 6 — Hybrid Expansion Multi-Seed Stability Report

**Verdict:** **INCONCLUSIVE — DO NOT SHIP**  
**Mode:** Isolated experiment only (production RAG / neighbor expansion / prompts / config defaults untouched)  
**Live run:** `hybrid_expansion_stability_results.json` → `meta.timestamp_utc` / `finished_utc`  
**Seeds:** `101`, `202`, `303` (Ollama `options.seed`, experiment-only HTTP path)

---

## 1. Executive Summary

Multi-seed validation **did not reproduce** Step 5’s single-run C_EVIDENCE lead (25.0/28). Across 3 documented seeds × Q1–Q7:

| Configuration | Mean total (/28) | Median | Std | Mean ctx chars | Mean neighbors |
|---|---:|---:|---:|---:|---:|
| OFF | 22.33 | 21 | 3.83 | 4405 | 0.00 |
| **BLIND** | **23.43** | 23 | **3.26** | 7687 | 6.29 |
| A_TABLE | 22.10 | 23 | 5.10 | 4990 | 1.14 |
| C_EVIDENCE | 22.00 | 23 | 5.00 | 5444 | 2.00 |
| **HYBRID_CAP2** | **22.86** | 23 | 5.01 | **5183** | **1.43** |
| HYBRID_CAP3 | 22.00 | 23 | 5.00 | 5288 | 1.71 |

**Key findings**

1. **C_EVIDENCE is not consistently better than BLIND** on mean quality (22.0 vs 23.4). Step 5’s 25.0 was inflated by a favorable single generation.
2. **HYBRID_CAP2** is the strongest *selective* arm: same Q1/Q3 gains as C, better Q5 than C, less context than BLIND — but it **regresses Q6** on 2/3 seeds (same failure mode as A/C).
3. **HYBRID_CAP3 does not improve on CAP2**; extra neighbors hurt Q5 utilization (categories present in context but omitted from answers).
4. **Answer variance is large** (especially Q2 and Q6). Seed control works at the API level, but different seeds still yield materially different answers at `temperature=0.2`.
5. **Insufficient evidence for production implementation.** Recommend a follow-up that gates expansion when required evidence is already in retrieved hits (Q6), then re-run ≥5 seeds.

Absolute scores must **not** be pooled with Step 3 (24.0 OFF) or Step 5 (21.0 OFF / 25.0 C) without noting run non-comparability (see §2).

---

## 2. Baseline Discrepancy Investigation

| Source | OFF mean (/28) | Notes |
|---|---:|---|
| Step 3 (`answer_level_eval_scores.json`) | **24.0** | Scored from `/tmp/rag_neighbor_live_validation.json` @ `2026-11-24T06:17:46Z` |
| Step 5 (`selective_expansion_scores.json`) | **21.0** | New live generations; n=1 per cell |
| Step 6 (this run) | **22.33** | Mean over 3 seeds |

### Did the rubric change?
**No.** All three steps use the same seven 0–4 metrics (correctness, completeness, evidence utilization, unsupported claims, conditions/exceptions, relevance, source consistency). `unsupported_claims`: higher = fewer unsupported claims.

### Did the answers differ?
**Yes.** Spot-check: Step 3 vs Step 5 OFF answers differ for Q1, Q2, Q3, Q5 (identical only for some stable cells such as one Q6 wording). Step 6 OFF again differs by seed (e.g. Q1 seed 101/303 include processing+15:00; seed 202 collapses to Standard Ground only).

### Does model variability explain the gap?
**Primarily yes.** Same model (`llama3.2`), prompt (`rag_system_prompt`), temperature (`0.2`), top_k (`5`), min_similarity (`0.5`), embeddings, and DB. Production `OllamaProvider` does **not** pass `seed`, so prior steps were uncontrolled stochastic draws. Step 6 confirms large cross-seed spread on Q1/Q2/Q6 even with documented seeds.

### Was scoring consistent?
Step 3/5 were human rubric applications to captured text. Step 6 uses **checklist-assisted scoring** aligned to the same evidence criteria (methods table, 3-step procedure, 7-calendar-day rule, category list, photographic evidence, etc.), not an LLM judge. Totals are comparable *within* Step 6; cross-step absolute means remain only directionally comparable.

### Generation settings identity
Held constant in Step 6 vs prior controlled runs: `llama3.2`, `nomic-embed-text`, production `rag_system_prompt`, `rag_temperature=0.2`, `top_k=5`, `min_similarity=0.5`, unchanged DB embeddings. Only expansion planner + (for Step 6) `options.seed` differ.

**Conclusion:** Do **not** combine Step 3/5/6 absolute scores into a single league table. Treat each run’s **relative** config ranking separately; use Step 6 for stability claims.

---

## 3. Experimental Methodology

1. Inspected Step 5 planners in `selective_strategies.py` (A_TABLE / C_EVIDENCE criteria unchanged except addition of `plan_hybrid`).
2. Semantic search **once per question** (`top_k=5`, `min_similarity=0.5`); verified `semantic_hits_identical_across_configs == true` for all Q1–Q7.
3. Applied experiment-only planners: OFF, BLIND (`plan_neighbors` window=1), A_TABLE, C_EVIDENCE (+ post-load relevance filter), HYBRID_CAP2, HYBRID_CAP3.
4. Built CONTEXT with production `build_context_blocks` / `format_context_blocks` when neighbors exist.
5. Generated answers via **direct** Ollama `/api/chat` with `options: {temperature: 0.2, seed: S}` — production provider left unchanged (no seed parameter on `LLMProvider.chat`).
6. Seed verification (pre-run): identical `seed=42` completions matched; different seeds can still diverge on longer RAG prompts.
7. Scored every seed×config×question with checklist-assisted Step 3 rubric (`hybrid_scoring.py`).

**Runs:** 6 configs × 7 questions × 3 seeds = **126** generations.

---

## 4. Hybrid Selection Logic

### Unchanged building blocks

**A_TABLE** (unchanged criteria): expand when retrieved text looks like an incomplete Markdown table (`|` density / truncated row / header with too few data rows). Prefer **next**; optional **previous** for headerless continuation.

**C_EVIDENCE** (unchanged criteria): expand on truncated chunks and/or overdue-definition gap missing `7 calendar days`; keep neighbors that are lexically relevant **or** pipe-heavy table continuations **or** contain the 7-calendar-day rule. Prefer **next**; previous only for lowercase remnants. Post-load relevance filter identical to Step 5.

### HYBRID (new, experiment-only)

1. Collect C_EVIDENCE candidates (over-fetch).
2. Union A_TABLE incomplete-table candidates not already selected (dedupe by `(document_name, chunk_index)`; keep C’s reason if both fire).
3. Priority sort: `overdue_section_gap` > `truncated_table` / `incomplete_table` > other `truncated_evidence` (by origin hit rank).
4. Apply C’s post-load relevance filter.
5. Hard cap: **CAP2 → 2 neighbors**, **CAP3 → 3 neighbors**.

Does **not** blindly concatenate all A∪C neighbors without dedupe, priority, filter, and cap.

---

## 5. Multi-Run Results

### Config aggregates (n=21 scores each = 7Q × 3 seeds)

| Config | Mean | Median | Std | Min | Max |
|---|---:|---:|---:|---:|---:|
| OFF | 22.33 | 21 | 3.83 | 17 | 28 |
| BLIND | 23.43 | 23 | 3.26 | 18 | 28 |
| A_TABLE | 22.10 | 23 | 5.10 | 10 | 28 |
| C_EVIDENCE | 22.00 | 23 | 5.00 | 10 | 28 |
| HYBRID_CAP2 | 22.86 | 23 | 5.01 | 10 | 28 |
| HYBRID_CAP3 | 22.00 | 23 | 5.00 | 10 | 28 |

### Seed determinism

Almost all question×config cells produced **3 distinct answers** across seeds `101/202/303` (Q4/Q7 more stable). Same seed is API-stable; cross-seed variance remains the dominant uncertainty.

---

## 6. Per-Question Comparison (mean total /28)

| Q | OFF | BLIND | A | C | HYB2 | HYB3 | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 19.7 | 22.3 | **23.7** | **23.7** | **23.7** | **23.7** | Table neighbor `#2` helps methods; processing still often dropped |
| Q2 | 22.7 | 20.0 | 22.7 | 22.7 | 22.7 | 22.7 | Full 3-step list only on ~1/3 seeds; BLIND worse |
| Q3 | 19.0 | 20.7 | 19.0 | **24.7** | **24.7** | **24.7** | C/Hybrid attach `#5` and state 7-day rule; A does not |
| Q4 | 26.0 | 26.0 | 26.3 | 26.0 | 26.0 | 26.0 | Stable |
| Q5 | 18.0 | **24.0** | **24.0** | 18.0 | **24.0** | 18.0 | Categories: A/BLIND/HYB2 often; C/HYB3 underuse `#1` |
| Q6 | **28.0** | **28.0** | **16.0** | **16.0** | **16.0** | **16.0** | Selective arms miss photo evidence on seeds 202/303 |
| Q7 | 23.0 | 23.0 | 23.0 | 23.0 | 23.0 | 23.0 | Stable |

---

## 7. Stability and Variance Analysis

| Question | Approx. per-seed std (typical) | Observation |
|---|---|---|
| Q1 | ~1.9 | Methods vs processing tradeoff by seed |
| Q2 | ~3.8 (0 for BLIND-collapsed) | One-line vs full 3-step procedure |
| Q3 | ~1.4–2.4 | C/Hybrid more complete but still variable wording |
| Q5 | 0–4.2 | Category list intermittent even when `#1` in context |
| **Q6** | **0 OFF/BLIND; ~8.5 selective** | Catastrophic selective failure on 2/3 seeds |

**Does C_EVIDENCE consistently beat BLIND?**  
**No.** Mean 22.0 < BLIND 23.4. C wins Q3; loses Q5 mean and Q6 badly; Q1 similar to other selective arms.

**Step 5 C=25.0:** explained by a lucky single draw (strong Q1/Q2/Q3 utilization without the Q6 miss). Multi-seed shows that draw was **not** stable.

---

## 8. Context-Efficiency Analysis

| Config | Mean chars | Max chars | Mean neighbors | Mean “irrelevant” neighbors* |
|---|---:|---:|---:|---:|
| OFF | 4405 | 4482 | 0.00 | 0.00 |
| BLIND | 7687 | 9457 | 6.29 | 5.86 |
| A_TABLE | 4990 | 5235 | 1.14 | 0.86 |
| C_EVIDENCE | 5444 | 6817 | 2.00 | 1.57 |
| HYBRID_CAP2 | 5183 | 5708 | 1.43 | 1.00 |
| HYBRID_CAP3 | 5288 | 6269 | 1.71 | 1.29 |

\*Same ground-truth-proxied heuristic as Step 5.

**Cap respect:** `cap_respected == true` for all HYBRID_CAP2 (≤2) and HYBRID_CAP3 (≤3) question cells.

**Efficiency vs quality:** HYBRID_CAP2 cuts ~33% mean characters vs BLIND with competitive selective coverage on Q1/Q3/Q5, but **does not** dominate BLIND on mean score because of Q6 regressions and Q2 seed noise.

**Duplicate content:** Hybrid dedupes A∩C keys before capping; no duplicate neighbor labels observed in planned sets.

---

## 9. Regression Analysis

### vs OFF (per-question mean, |Δ|≥1)

| Config | Improvements | Regressions | Critical regression |
|---|---:|---:|---|
| BLIND | Q1, Q3, Q5 | Q2 | — |
| A_TABLE | Q1, Q5 | **Q6 (−12)** | Photo evidence miss |
| C_EVIDENCE | Q1, Q3 | **Q6 (−12)** | Photo evidence miss |
| HYBRID_CAP2 | Q1, Q3, Q5 | **Q6 (−12)** | Photo evidence miss |
| HYBRID_CAP3 | Q1, Q3 | **Q6 (−12)**; Q5 flat | Photo + Q5 dilution |

### vs BLIND

| Config | Improvements | Regressions |
|---|---:|---:|
| A_TABLE | Q1, Q2 | Q5≈tie/mixed, **Q6** |
| C_EVIDENCE | Q2, Q3 | Q5, **Q6** |
| **HYBRID_CAP2** | Q1, Q2, Q3 | **Q6** (Q5 ≈ BLIND mean) |
| HYBRID_CAP3 | Q1, Q2, Q3 | Q5, **Q6** |

### Focused answers

1. **Q1 delivery completeness:** Selective table expansion (A/C/Hybrid) improves method coverage vs OFF; still rarely states all of methods+processing+15:00 together across seeds.
2. **Q2 procedure completeness:** Unstable. Full 3-step appears on ~1/3 seeds for OFF/A/C/Hybrid; BLIND usually collapses.
3. **Q3 seven-day rule:** C and both Hybrids consistently attach `delivery_policy.md#5` and usually state the rule; A does not (wrong-table expansion).
4. **Q5 categories:** A and HYBRID_CAP2 often list categories; C and HYBRID_CAP3 underuse `#1` despite presence (extra neighbors dilute).
5. **Q6 A_TABLE regression:** Confirmed and **shared by C and Hybrid** on seeds 202/303 — model cites restocking-fee neighbor text and claims no evidence requirement. OFF/BLIND stay perfect (28).

---

## 10. Recommended Production Strategy

**Do not implement selective or hybrid expansion in production yet.**

If a next experiment is approved, prioritize:

1. **Q6 guard:** skip expansion when photographic-evidence language is already in a retrieved hit.
2. Prefer **HYBRID_CAP2** (not CAP3) as the selective candidate — best balance of Q1/Q3/Q5 coverage and context size among selective arms.
3. Re-run **≥5 seeds** (or seed + temperature grid) with the guard in place.
4. Gate production on: mean ≥ BLIND, **no Q6 mean regression**, and Q3 7-day communication retained.

BLIND remains a coverage tool, not a quality default.

---

## 11. Limitations

1. Only **3** seeds (minimum required); 5 preferred but deferred after clear Q6 blocker.
2. Checklist-assisted scoring is aligned to Step 3 evidence criteria but is not a second independent human panel.
3. “Irrelevant neighbor” metric remains ground-truth-proxied.
4. Seed is experiment-only; production chat path still has no seed control.
5. Did not modify prompts, chunking, or retrieval — generation underuse remains a large confounder.
6. Step 3/5 absolute scores not pooled into Step 6 means.

---

## 12. Final Verdict

### **INCONCLUSIVE — DO NOT SHIP**

| Decision question | Answer |
|---|---|
| 1. Is C_EVIDENCE consistently better than BLIND? | **No** (22.0 < 23.4 mean; Q6 regression) |
| 2. Does hybrid improve on C_EVIDENCE? | **CAP2 slightly** on mean + Q5; **CAP3 no** |
| 3. Does table completion improve Q1 without harming Q6? | **Q1 yes; Q6 still harmed** (shared selective failure) |
| 4. Which neighbor cap is better? | **CAP2** (better Q5, less context than CAP3) |
| 5. Are results stable across runs? | **No** — high Q2/Q5/Q6 seed variance |
| 6. Enough evidence for production? | **No** — recommend guarded follow-up experiment |

### Files created or modified (experiment only)

| File | Role |
|---|---|
| `experiments/retrieval_eval/selective_strategies.py` | Added `plan_hybrid` (A/C criteria unchanged) |
| `experiments/retrieval_eval/run_hybrid_stability_experiment.py` | Multi-seed harness (OFF/BLIND/A/C/HYBRID caps) |
| `experiments/retrieval_eval/hybrid_scoring.py` | Checklist-assisted Step 3 rubric scorer |
| `experiments/retrieval_eval/hybrid_expansion_stability_results.json` | Raw multi-seed answers + context stats |
| `experiments/retrieval_eval/hybrid_expansion_stability_scores.json` | Per-seed scores + aggregates |
| `experiments/retrieval_eval/HYBRID_EXPANSION_STABILITY_REPORT.md` | This report |

### Unchanged confirmation

During this Step 6 experiment:

- Production RAG code, prompts, configuration **defaults**, semantic search, production neighbor expansion, chunking, PostgreSQL records, embeddings, Q1–Q7 ground truth, and prior Step 3/4/5 reports/baselines were **not** modified for production behavior.
- Only isolated files under `experiments/retrieval_eval/` were added or extended.
- Hybrid / selective logic was **not** deployed.

**Stop.** Awaiting approval before any further production-oriented work.
