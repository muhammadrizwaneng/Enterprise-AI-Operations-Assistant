# Step 12A — GENERAL Expansion Trigger Attribution Analysis

**Mode:** READ-ONLY investigation (no code, data, experiment, or historical-file changes)  
**Primary sources:** `evidence_guard.py` (frozen SHA-256 `4ab51eb2…eae6`), `selective_strategies.py` helpers, Step 11 `step11_results.json` (H2 Q28–Q47), Step 8/9 artifacts, Step 10/11 reports  
**Labels:** CONFIRMED / LIKELY / UNCONFIRMED / INSUFFICIENT DATA

---

## 1. Executive Summary

Step 11 removed GENERAL `_chunk_truncated` and saw **0/20 skip-decision changes** because GENERAL incompleteness is an **OR across three per-hit detectors**, evaluated with **`any(hit in top-5)`**. On H2’s 15 `general` questions, every item had truncation **and** at least one of table-incomplete or procedure-needs-next; **0/15** had truncation-only incompleteness.

| Finding | Label |
|---|---|
| GENERAL expands unless (coverage ≥ 0.6) **and** no incompleteness on **any** hit | **CONFIRMED** (`evidence_guard.py` 354–379) |
| Incompleteness = table_incomplete **OR** procedure_needs_next **OR** chunk_truncated | **CONFIRMED** |
| H2 GENERAL: trunc 15/15, table 13/15, procedure 11/15; combos only `T+Tab`, `T+Proc`, `T+Tab+Proc` | **CONFIRMED** (recomputed from live top-5 matching recorded hits) |
| Single-signal removal of trunc, table, **or** procedure alone → still **0/15** GENERAL skips on H2 (counterfactual) | **CONFIRMED** (logic replay; not a new live ablation) |
| Table/procedure often fire on **non-primary** distractor hits while answer facts already sit in top-5 | **CONFIRMED** (8/15 table-only-on-non-primary; 9/15 proc-only-on-non-primary) |
| HYBRID neighbors on H2 almost never equal primary labels; OFF already scored ~28 for most items | **CONFIRMED** |

**Bottom line:** Truncation was not uniquely causal. The architecture that forces expansion is **any-hit OR-incompleteness**, especially **distractor** table/procedure signals under 500-char windows—not a single named detector.

**Do not implement the next ablation in this step.**

---

## 2. Step 11 Findings Recap

From `GENERAL_TRUNCATION_ABLATION_REPORT.md` (unchanged):

| Config | Mean total |
|---|---:|
| HYBRID_CAP2 | 28.0 |
| GENERAL_NO_TRUNCATION | 28.0 |

- Skip divergences frozen vs ablation: **0/20**
- Questions with truncation-only incompleteness: **0/20**
- Specialized skips only: Q45 (`requirement_evidence`), Q46 (`procedure`)
- Repeating truncation-only ablation: low research value

---

## 3. GENERAL Decision Architecture

After `classify_evidence_need(question)` returns `general` (`evidence_guard.py` 97–…, 354+):

```
coverage = fraction of question terms present in joined top-5 text
incomplete = any(
    table_incomplete(hit) OR procedure_needs_next(hit) OR chunk_truncated(hit)
    for hit in top-5
)
SUFFICIENT (skip expansion)  iff  coverage >= 0.6  AND  not incomplete
else INSUFFICIENT (allow HYBRID_CAP2)
```

**Gate structure (CONFIRMED):**

1. **Lexical coverage** — conjunctive gate (≥ 0.6 required to skip).
2. **Incompleteness OR** — three detectors; **any hit**, **any detector** blocks skip.
3. Detectors are **combined with OR**, not scored/weighted.
4. Default when unsure: expand (`general_insufficient_default`).

Non-GENERAL needs use separate checkers; this report focuses on GENERAL, with non-GENERAL H2 rows noted for completeness.

---

## 4. Complete Trigger Inventory

| Signal | Function | Triggering condition (summary) | Input examined | Independent? | Can alone force expand? | Overlap |
|---|---|---|---|---|---|---|
| `low_lexical_coverage` | inline in `assess_evidence_sufficiency` | coverage &lt; 0.6 | question tokens ∩ joined hit text | Conjunctive with incompleteness for *skip*; alone forces expand if coverage low even when complete | **Yes** | Uses same `_question_terms` as hybrid planner |
| `chunk_truncated` | `_chunk_truncated` | len ≥ 480 and ends mid-token / mid-cell (not `.!?:"\|`) | per-hit `chunk_text` | OR’d with others | **Yes** (if others false) | Overlaps table rule for long pipe-heavy chunks ending alnum |
| `table_incomplete` | `_table_appears_incomplete` | looks like table (`|`≥4 etc.) **and** (mid-row cut **or** len≥480 ends alnum **or** named header with &lt;3 data rows) | per-hit `chunk_text` | OR’d | **Yes** | Shares “long + ends alnum” idea with truncation |
| `procedure_needs_next` | `_procedure_needs_next` | overdue def without 7-day rule; **or** numbered list ≥450 chars ending mid-sentence; **or** “Support agents must” with &lt;3 steps (unless 7-day complete) | per-hit `chunk_text` | OR’d | **Yes** | Distinct keywords; still OR with trunc/table |

Source lines: `evidence_guard.py` 354–379; `selective_strategies.py` 70–119, 168–179.

**Not GENERAL triggers (out of scope but present in file):** specialized need checkers for `requirement_evidence`, `procedure`, `duration_table`, `eligibility`, `contact_support`.

---

## 5. Individual Signal Analysis

### 5.1 Lexical coverage

- On H2 GENERAL: **0/15** had coverage &lt; 0.6 (min observed 0.60 on Q36).
- Therefore coverage did **not** independently drive any H2 GENERAL expansion.
- **Label:** CONFIRMED for H2 frequency; importance on other splits INSUFFICIENT DATA.

### 5.2 `chunk_truncated`

- True for nearly all 500-char mid-document windows that do not end on punctuation.
- Step 11 ablation: removing it → **0 decision changes** (recorded).
- **Label:** CONFIRMED pervasive; CONFIRMED not uniquely decisive on H2.

### 5.3 `table_incomplete`

- Requires `_looks_like_table` first; then cut-row / long-alnum-end / thin header-table heuristics.
- Can fire on a **complete answer elsewhere in top-5** if **any other** hit looks like a cut table (e.g. Q28 primary answer in `delivery_policy.md#5`; table signal from unrelated `refund_policy.md#2`).
- Can also fire on the answering chunk when that chunk itself embeds a cut warranty/status table (Q40, Q41).
- **Label:** CONFIRMED can be distractor-driven; LIKELY overly conservative under `any(hit)`.

### 5.4 `procedure_needs_next`

- Tied to numbered lists / overdue / “Support agents must”, often true when a 500-char window cuts a list mid-sentence (ends without `.!?:`).
- Example Q36: answer email is complete in short `privacy_policy.md#7` (138 chars, no incompleteness); expansion still allowed because distractors `employee_handbook.md#4` and `privacy_policy.md#2` set `procedure_needs_next`.
- **Label:** CONFIRMED can be distractor-driven; does distinguish some complete overdue lists (7-day short-circuit) but still flags many cut lists.

---

## 6. Signal Frequency Analysis

Recomputed against live retrieval; **all 20 questions’ hit labels matched Step 11 recorded `semantic_hits`**.

### 6.1 Per-question table (H2)

| QID | Need | Triggered GENERAL signals | Combo | Frozen skip | Ablation skip | Step11 Δ | HYBRID nbr | Notes |
|---|---|---|---|---|---|---|---:|---|
| Q28 | general | trunc, table | T+Tab | no | no | no | 2 | table on non-primary only |
| Q29 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 1 | |
| Q30 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 0 | |
| Q31 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 0 | |
| Q32 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 1 | proc on primary+# |
| Q33 | duration_table | *(specialized path)* | — | no | no | no | 0 | not GENERAL |
| Q34 | duration_table | *(specialized)* | — | no | no | no | 1 | not GENERAL |
| Q35 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 1 | |
| Q36 | general | trunc, proc | T+Proc | no | no | no | 2 | proc distractors only |
| Q37 | general | trunc, table | T+Tab | no | no | no | 1 | |
| Q38 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 1 | OFF 26.4→HYB 28 |
| Q39 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 1 | |
| Q40 | general | trunc, table | T+Tab | no | no | no | 1 | table on primary |
| Q41 | general | trunc, table | T+Tab | no | no | no | 0 | expect neighbor; OFF already 28 |
| Q42 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 2 | |
| Q43 | general | trunc, proc | T+Proc | no | no | no | 1 | proc distractors only |
| Q44 | general | trunc, table, proc | T+Tab+Proc | no | no | no | 2 | proc on primary |
| Q45 | requirement_evidence | *(specialized)* | — | **yes** | **yes** | no | 1† | skip; HYBRID still expands |
| Q46 | procedure | *(specialized)* | — | **yes** | **yes** | no | 2† | skip |
| Q47 | procedure | *(specialized)* | — | no | no | no | 1 | specialized insufficient |

† Neighbor count shown for HYBRID_CAP2 config; guarded/ablation skips use 0 neighbors.

**Low lexical coverage:** 0/15 GENERAL.

### 6.2 Frequencies (GENERAL only, n=15)

| Signal | Questions triggering | Rate |
|---|---:|---:|
| `chunk_truncated` | 15 | 100% |
| `table_incomplete` | 13 | 86.7% |
| `procedure_needs_next` | 11 | 73.3% |
| `low_lexical_coverage` | 0 | 0% |

---

## 7. Signal Co-occurrence Analysis

### 7.1 Observed GENERAL combos (n=15)

| Combination | Count | IDs |
|---|---:|---|
| T+Tab+Proc | 9 | Q29–Q32, Q35, Q38, Q39, Q42, Q44 |
| T+Tab | 4 | Q28, Q37, Q40, Q41 |
| T+Proc | 2 | Q36, Q43 |
| T only / Tab only / Proc only / none | **0** | — |

### 7.2 Counterfactual: disable signal(s), keep OR + coverage gate

Replay on the same H2 GENERAL hit flags (not a shipped experiment):

| Remove from incompleteness OR | GENERAL that would skip |
|---|---|
| trunc only (Step 11) | **0/15** |
| table only | **0/15** |
| procedure only | **0/15** |
| trunc + table | 4/15 (Q36, Q43 + … only if proc also absent — actually T+Tab cases need proc cleared: **2/15** wait) |

Corrected from replay script:

| Remove | would_skip |
|---|---|
| trunc | 0/15 |
| table | 0/15 |
| proc | 0/15 |
| trunc+table (leave proc) | **2/15** (Q36, Q43 — T+Proc only) |
| trunc+proc (leave table) | **4/15** (Q28, Q37, Q40, Q41 — T+Tab only) |
| table+proc (leave trunc) | **0/15** |
| all incompleteness | 15/15 |

**CONFIRMED:** Why Step 11 was null — every GENERAL question retained table and/or procedure after trunc removal.  
**CONFIRMED:** On **this** H2 set, **any single incompleteness ablation is also predicted null**.

### 7.3 Primary vs non-primary locus (GENERAL)

| Pattern | Count / 15 |
|---|---:|
| `table_incomplete` only on non-primary hit(s) | **8** |
| `table_incomplete` on primary | 5 |
| `procedure_needs_next` only on non-primary | **9** |
| `procedure_needs_next` on primary | 2 |

---

## 8. Table Signal Investigation

**What it is:** Heuristic over pipe-heavy markdown; flags cut rows, long chunks ending alnum, or thin Method/Category/Order-Status tables (`selective_strategies.py` 74–95).

**Actual incomplete tables?** Often **yes for the flagged chunk** (e.g. `refund_policy.md#2` ends mid-row: `...| returned`). That does **not** mean the *question’s* answer table is incomplete.

**Can a complete answer still trigger expansion?** **Yes (CONFIRMED).** Q28: address-change rule fully present in `delivery_policy.md#5`; incompleteness from unrelated refund status table `#2`.

**Unrelated table content?** **Yes (CONFIRMED).** Q38: payment-card fact in `privacy_policy.md#1`; table signal from `customer_support_guidelines.md#0` category header table cut at `| bill`.

**Does added context improve completeness on H2?** Mostly **no score gain** (OFF already 28). Exception: Q38 OFF mean 26.4 → HYBRID 28 via `customer_support_guidelines.md#1` neighbor — **not** clearly because the original card-number sentence was missing (it was in `#1`); seed variance under OFF is the recorded difference. Treat causal neighbor benefit as **LIKELY/seed-driven**, not proven necessary evidence.

---

## 9. Procedure Signal Investigation

**What it is:** Numbered-step / overdue / “Support agents must” incompleteness heuristics (`selective_strategies.py` 102–119).

**Incomplete vs complete:** Partial — short-circuits when `7 calendar days` + numbered steps; still flags many cut lists that continue next chunk.

**Unnecessary keyword-ish expansion?** Not bare keywords alone; requires numbered steps + length/ending or overdue-without-7-day. Still **over-fires relative to question need** when the flagged list is off-topic (Q36 security-email question vs ticket-handling list in handbook).

**Does expansion add missing steps?** On H2 GENERAL items with OFF=28, neighbors were **not** required for rubric facts. Q32/Q44: procedure signal can appear **on the primary chunk itself** because the status/ticket list is cut at 500 chars—even though the asked fact (“no open→closed without resolution note”; “4 business hours”) is already inside that chunk.

**Irrelevant instructions?** **CONFIRMED possible.** HYBRID neighbors for Q36 are other privacy chunks; for Q39 a refund table neighbor—neither is the backorder quantity fact (already in primary). Blind on Q46 (specialized procedure question) dropped to 16/28 with distracting ±1 neighbors (Step 11), showing expansion risk when neighbors are wrong.

---

## 10. Original Evidence Sufficiency

Oracle used here: offline primary labels ⊆ semantic top-5 **and** OFF answer mean (rubric), distinguished from keyword signals.

| Pattern | Evidence |
|---|---|
| All H2 primaries in top-5 | Step 11 `offline_primary_coverage.all_primary_retrieved` true for recorded H2 set (probe/report) |
| OFF mean 28 on 19/20 questions | Step 11 results; Q38 OFF 26.4 only soft miss |
| Keyword incompleteness true while OFF already complete | **15/15 GENERAL** still expand |

**CONFIRMED:** On H2, GENERAL signals systematically disagree with “original top-5 already answerable” as measured by OFF scores + primary coverage.

**Caveat:** H2 has a **score ceiling**; OFF≈28 does not prove neighbors never help on harder items (see Q19 historically).

---

## 11. Neighbor Usefulness Analysis

From Step 11 HYBRID_CAP2 neighbor labels vs primary labels:

- **Useful neighbors (label ∈ primary):** **0/20 questions** had any HYBRID neighbor equal to a primary chunk label.
- **Distracting / non-primary neighbors:** present whenever `nbr_count > 0` (majority of rows).
- **Score delta HYBRID−OFF:** 0.0 on 19/20; **+1.6 on Q38 only**.
- Annotated `expects_neighbor_helpful` Q41/Q47: both OFF=28 anyway; HYBRID added 0 useful-primary neighbors.

**CONFIRMED for H2:** expansion rarely adds *primary* chunks (they are already retrieved); it adds **adjacent** chunks. Those adjacents were **redundant for the rubric** on almost all H2 items, sometimes merely harmless under the checklist scorer.

**Do not claim** neighbors are always useless globally — Q19 (below) shows the opposite failure mode (need a missing primary neighbor, selective hybrid picks wrong ones).

---

## 12. Q6 and Q19 Historical Case Studies

### 12.1 Q6 (Step 8) — restocking-fee distraction

- Need: `requirement_evidence` (**not GENERAL**).
- Guard **skipped**; HYBRID without guard pulled `refund_policy.md#5` / `#3` and mean fell to **17.2** vs GUARDED/OFF **28** (`guarded_hybrid_results.json`).
- Relation to GENERAL signals: Q6’s win was a **specialized** sufficiency path. It does **not** prove GENERAL truncation/table/proc logic is well calibrated—it shows **skipping expansion can avoid harmful neighbors** when a specialized check fires.
- **CONFIRMED** as specialized-path success; **not** a GENERAL-signal validation.

### 12.2 Q19 (Step 9) — ticket statuses

- Need recorded: **`general`** with incompleteness_signals; skip false.
- Primary `#4` **missing** from top-5; OFF/HYBRID/GUARDED **16**; BLIND **28** by taking `#3±1` including `#4`.
- Hit-level recomputation on recorded Q19 hits:
  - `#3` (partial status list): trunc/table/proc **all false**
  - Distractors `#0,#1` (tables), `#2` (table), `employee_handbook.md#4` (proc): drive incompleteness OR
- HYBRID neighbors: `refund_policy.md#3`, `customer_support_guidelines.md#2` — **wrong** for statuses; GUARDED identical because GENERAL did not skip.

**CONFIRMED:** GENERAL correctly *allowed* expansion (evidence incomplete), but **table-oriented hybrid origins** selected poor neighbors. Blind’s unselective ±1 on the right hit recovered `#4`.

**Relation to Step 11:** H2 items mostly already had primaries in top-5 (unlike Q19), so the same “always expand on distractor table/proc” behavior looked **harmless** under a ceiling scorer—masking the Q19-type failure and the Q6-type distraction risk.

---

## 13. Why Step 11 Had Zero Effect

Causal chain (**CONFIRMED**):

1. GENERAL incompleteness = OR(trunc, table, proc) over **any** top-5 hit.
2. Step 11 deleted only trunc from that OR.
3. On H2 GENERAL, every question still had table and/or proc true (combos T+Tab, T+Proc, or all three; **no T-only**).
4. Coverage was already ≥ 0.6, so the only way to skip was clearing incompleteness — which trunc removal did not do.
5. Therefore skip decisions identical → same expand/skip → for 18/20 questions identical HYBRID contexts; Q45/Q46 skips were specialized (unchanged by trunc ablation).

---

## 14. Confirmed Root Causes

1. **Any-hit aggregation** — one distractor incomplete chunk forces expand even if the answering chunk is complete.  
2. **OR composition of three detectors** — single-signal ablation is structurally weak when co-occurrence is high.  
3. **500-char windowing** — makes trunc + cut-table + cut-list extremely common.  
4. **Table/procedure detectors are chunk-local, not question-conditioned** — off-topic cut tables/lists count the same as on-topic ones.  
5. **Classification gap** (from Step 10, still true on H2) — most fact questions fall into GENERAL, so these heuristics dominate.

---

## 15. Unconfirmed Hypotheses

| Hypothesis | Status |
|---|---|
| Table signal is *more* harmful than procedure on average | **UNCONFIRMED** (H2 ceiling; no factorial live ablation) |
| Scoping incompleteness to top-1 / max-similarity hit would raise skip rate without Q19-like regressions | **LIKELY** mechanism, **UNCONFIRMED** empirically |
| Removing table+proc together would improve net quality | **INSUFFICIENT DATA** (counterfactual skips 0 if trunc remains) |
| Lexical coverage threshold 0.6 is well calibrated | **INSUFFICIENT DATA** (never binding on H2 GENERAL) |

---

## 16. Recommended Next Ablation

**Do not** run another single-signal incompleteness ablation on an H2-like mix expecting decision movement — counterfactual predicts **null** for trunc, table, or proc alone.

**Preferred next experiment (still approval-gated; not implemented here):**

### Option A (highest leverage) — **Any-hit scope ablation**

Compare GENERAL incompleteness computed on:

- **ALL_HITS** (current), vs  
- **TOP1_ONLY** or **TOP_M_BY_SIM** (e.g. M=1 or 2), vs  
- **MAX_SIM_DOC_ONLY** (hits from the top document only).

This attacks root cause (1) without deleting detectors that may still matter for true cut tables/procedures on the answering span.

### Option B — **Table-signal ablation on a stratified set**

If a single *named* signal must be chosen first: **`table_incomplete`**.

Rationale: highest clear distractor-only rate among remaining signals (8/15 GENERAL table-only-on-non-primary); hybrid reasons frequently `truncated_table_next` / `incomplete_table_next`; Q19 wrong neighbors were table-originated.

**Require** a new split with **table-only** and **procedure-only** incompleteness strata (see §17), or the ablation will likely repeat Step 11’s null.

---

## 17. Dataset Requirements for Next Experiment

Need a **new** independent split (not Q1–Q7, Q8–Q27, Q28–Q47) with pre-registered strata:

| Stratum | Requirement |
|---|---|
| Answer already in top-5; incompleteness **only** from non-primary table | Measure FP expand / distraction |
| Answer already in top-5; incompleteness **only** from non-primary procedure | Same for proc |
| Truncation-only incompleteness (if corpus allows; H2 had **0**) | Isolate trunc |
| True multi-chunk gap (Q19-like): primary neighbor missing from top-5 | Measure FN skip risk if scope narrows |
| Specialized procedure / requirement phrasing | Ensure specialized paths unchanged |
| Non-ceiling items (OFF &lt; 28 common) | Avoid H2 ceiling blindness |

Also log per-hit signal locus (primary vs not) and neighbor∩primary — as in this attribution — **without** feeding labels into the guard.

---

## 18. Final Verdict

### Final questions

1. **Which GENERAL signals independently trigger expansion?**  
   Each of: `low_lexical_coverage`, `chunk_truncated`, `table_incomplete`, `procedure_needs_next` **can** independently force expand when others are false (**CONFIRMED** in code). On H2, only the three incompleteness detectors fired in combination; coverage never acted alone.

2. **Which signals most frequently co-occur?**  
   On H2 GENERAL: **truncation + table + procedure** (9/15); then **trunc+table** (4); **trunc+proc** (2). Truncation co-occurs with ≥1 other incompleteness signal on **15/15**.

3. **Which signals appear overly conservative?**  
   **`table_incomplete` and `procedure_needs_next` under any-hit aggregation** — especially when only non-primary hits fire (**CONFIRMED** examples Q28, Q36, Q38, Q39). Truncation is pervasive but was already shown non-unique (Step 11).

4. **Which signals are important for genuinely incomplete evidence?**  
   **LIKELY:** cut tables/lists on the *answering* span (Q40/Q41-style; Q19-style missing continuation). **INSUFFICIENT DATA** to rank detectors without a Q19-rich, non-ceiling set. Specialized non-GENERAL checkers (not these GENERAL signals) mattered for Q6/Q45/Q46 skips.

5. **Why did removing truncation have no effect?**  
   OR-incompleteness still true via table and/or procedure on every H2 GENERAL question (**CONFIRMED**).

6. **Which single signal should be investigated first in the next ablation?**  
   Prefer **scope ablation (any-hit → top-M)** first. If constrained to one named detector: **`table_incomplete`**, on a **stratified** new split—not another H2-like mix.

7. **What fresh evaluation data will be needed?**  
   New IDs beyond Q47; strata in §17; non-ceiling scoring headroom; explicit Q19-like neighbor-gap slice; per-hit signal locus logging.

8. **Risks of removing that signal / narrowing scope?**  
   - **Table removal:** may miss true cut tables spanning chunks; could under-expand.  
   - **Top-M scope:** may **fail to expand** when the incomplete continuation is ranked below M but needed (Q19-like if the incomplete hit isn’t top-M—or conversely may still expand for wrong reasons if top-M is a distractor table).  
   - **Either change:** risk of Q6-like distraction if expand still happens with bad hybrid origins; risk of false skips if sufficiency is assumed too early.

---

**Stop.** No ablation implemented. Awaiting review before any Step 12B experiment.
