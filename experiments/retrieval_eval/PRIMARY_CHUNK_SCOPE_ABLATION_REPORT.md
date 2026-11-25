# Step 12B — Primary-Chunk-Scoped Signal Ablation Report

**Status:** **STOPPED — dataset not ready**  
**Experiment executed:** **No** (no TOP_M implementation, no A/B eval, no candidate freeze)  
**Readiness detail:** `experiments/retrieval_eval/step12b_primary_chunk_scope/DATASET_READINESS.md`  
**Isolation dir:** `experiments/retrieval_eval/step12b_primary_chunk_scope/` (readiness only)

No production RAG, frozen guard, embeddings, or Step 8–12A artifacts were modified.

---

## 1. Executive Summary

Step 12B asked whether restricting GENERAL incompleteness checks to top-M ranked hits reduces unnecessary expansion without harming neighbor-needed cases, using a **dev set A → freeze M → held-out B** protocol.

After inspecting the six NovaForge policy documents (~46 chunks), prior Q1–Q47 coverage, and live retrieval probes for unused facts, the corpus **cannot** support two **genuinely independent**, strata-complete, independently verified datasets without inventing ground truth or recycling prior evaluation topics.

**Therefore the ablation was not run.** Reporting numeric “results” for TOP_M_1/2/3 would be misleading.

| Gate | Result |
|---|---|
| Independent Dataset A + B | **FAIL** |
| Required strata on both sets | **FAIL** (especially neighbor-needed / genuinely incomplete) |
| Verified GT without invention | **Cannot meet volume** |
| Proceed to live TOP_M eval | **NO** |

---

## 2. Research Question

Does restricting GENERAL signal evaluation to the highest-ranked retrieved chunks reduce unnecessary expansion while preserving expansion for genuinely incomplete evidence?

**Answer from this step:** **Not estimable** on the current corpus under the required A/B protocol. The question remains open pending richer independent data (§19).

---

## 3. Step 12A Findings Recap

From `GENERAL_EXPANSION_TRIGGER_ATTRIBUTION_REPORT.md` (unchanged):

- GENERAL expands unless coverage ≥ 0.6 and no table / procedure / truncation signal on **any** top-5 hit.
- H2 GENERAL (n=15): only combos `T+Tab+Proc`, `T+Tab`, `T+Proc`; truncation on all 15.
- Table/procedure often fire on **non-primary** distractors while OFF ≈ 28.
- Single-signal ablation predicted null on H2; recommended **scope (top-M)** ablation **only with a stratified new split**.

Step 12B is that proposed scope study — blocked at the dataset gate Step 12A implicitly required.

---

## 4. Experimental Design

### Planned (not executed)

| Config | Intended behavior |
|---|---|
| OFF / BLIND / HYBRID_CAP2 | Unchanged baselines |
| BASELINE | Frozen any-hit GENERAL (top-5) + HYBRID_CAP2 if expand |
| TOP_M_1 / TOP_M_2 / TOP_M_3 | Same detectors; incompleteness `any()` only over ranks 1…M; coverage still over full top-5; specialized paths unchanged |

**Planned top-M rule (documented for future use, not implemented):**  
After semantic search returns hits ordered by similarity descending, GENERAL incompleteness detectors run only on `hits[:M]`. Lexical coverage continues to use all top-5 joined text. Classification and HYBRID_CAP2 planner unchanged.

**Protocol:** Compare M on Dataset A → freeze one M → evaluate once on Dataset B.

### Actually performed

1. Corpus + prior-question inventory  
2. Unused-chunk / remaining-atom mining with string verification  
3. Retrieval probes for scope-sensitive and neighbor-gap strata  
4. Readiness stop  

---

## 5. Dataset Independence

| Check | Outcome |
|---|---|
| Disjoint from Q1–Q7 / Q8–Q27 / Q28–Q47 topics | **Insufficient** unused high-value facts |
| Two sets without cross-tuning leakage | **Not achievable** at required strata depth |
| Independently verified GT | Remaining atoms exist (~15) but too few for A∪B×9 strata |
| New source documents | **None** in embeddings |

**CONFIRMED:** 33/46 chunks already used as primary in prior eval; many “new” probes duplicate Q4/Q10–Q12/Q16/Q21–Q22/Q25 facts.

---

## 6. Development Dataset Analysis

**Not built.** No Dataset A questions were finalized.

Probe-level observation (not an eval result): among ~22 candidate phrasings on remaining/overlapping facts, only ~9 showed “top-1 signal-clean / lower ranks dirty,” and only ~2–3 showed primary missing from top-5. That volume is inadequate to select M reliably.

---

## 7. Configuration Comparison

**Not run.** No scores for OFF, BLIND, HYBRID_CAP2, BASELINE, or TOP_M_*.

---

## 8. Signal Attribution by Chunk Rank

**No new live attribution table for A/B** (sets do not exist).

Historical support for the *hypothesis* (not a Step 12B measurement): Step 12A showed table-only-on-non-primary in 8/15 and procedure-only-on-non-primary in 9/15 H2 GENERAL questions — i.e. lower-ranked / non-answering hits often drive `any(hit)` incompleteness. That motivates top-M but does **not** substitute for A/B measurement.

---

## 9. Lower-Ranked Distractor Analysis

**Not run on A/B.**  

Readiness probes illustrated the intended phenomenon (e.g. answering chunk rank-1 clean while ranks 2–5 carry truncated tables/procedures) on a **handful** of leftover facts — too few to populate both development and held-out distractor strata without reuse.

---

## 10. Neighbor Evidence Usefulness

**Not measured** for Step 12B.

Prior evidence (Step 9 Q19; Step 11 H2) shows neighbor usefulness is **question-dependent** and that H2 under-represented true neighbor gaps. Proceeding without enough neighbor-needed items would bias TOP_M toward “always skip more” without testing false-skip risk.

---

## 11. Development Statistical Analysis

**N/A — no development runs.**

---

## 12. Selected Candidate and Freeze Details

**No candidate selected. No M frozen.**

Any claim of a preferred M would violate the protocol (selection requires Dataset A results).

---

## 13. Fresh Held-Out Validation

**Not performed.** Dataset B was not constructed (and must not be filled with recycled Q1–Q47 topics).

---

## 14. Failure Cases

**Experiment-level failure:** dataset readiness gate failed.  

No per-question TOP_M failure cases exist because eval did not run.

---

## 15. Historical Comparison

| Prior step | Relevance to 12B stop |
|---|---|
| Step 10 | GENERAL over-conservative; classification weak |
| Step 11 | Truncation-only ablation null; H2 ceiling |
| Step 12A | Any-hit OR + distractor table/proc; recommended top-M **with stratified new data** |
| Step 12B | Attempted that experiment; **blocked** by corpus exhaustion |

Do **not** treat H2 means as a stand-in validation of TOP_M.

---

## 16. Confirmed Findings

1. **CONFIRMED:** Current corpus is **not ready** for the mandated dual-dataset TOP_M protocol.  
2. **CONFIRMED:** Remaining verified unused factual atoms (~15) are insufficient for two full 9-stratum sets.  
3. **CONFIRMED:** Several attractive probe questions collide with prior Q IDs/topics.  
4. **CONFIRMED:** Neighbor-gap candidates among leftovers are rare (~2–3 in probe).  
5. **CONFIRMED:** No TOP_M code was added; frozen Step 8 guard hash left untouched.  
6. **NOT ESTABLISHED:** Whether TOP_M_1/2/3 improves quality or harms neighbor-needed items.

---

## 17. Limitations

- Readiness used the same embedded six documents as all prior steps.  
- Atom counts are approximate (some facts partially appear in used chunks).  
- Probe rankings depend on current `nomic-embed-text` retrieval; they illustrate scarcity, not final labels.  
- Stopping avoids false precision but leaves the research question unanswered empirically.

---

## 18. Final Verdict

### Final questions

1. **Do lower-ranked chunks cause unnecessary GENERAL expansion?**  
   **LIKELY historically (Step 12A), not re-measured here.** Cannot confirm rate on a valid 12B A/B set.

2. **Does TOP_M restriction reduce unnecessary expansion?**  
   **INSUFFICIENT DATA** — experiment not run.

3. **Which M performed best on development?**  
   **None selected** — Dataset A not built.

4. **Does the selected M preserve expansion when neighboring evidence is necessary?**  
   **N/A** — no freeze; neighbor-needed stratum not adequately available.

5. **Does the result generalize to fresh held-out questions?**  
   **N/A** — no held-out run.

6. **Is the improvement statistically and practically meaningful?**  
   **N/A** — no paired scores.

7. **Is the candidate reliable enough to justify another independent validation?**  
   **No candidate.** First priority is **dataset expansion**, not another ablation on the same six files.

**Shipping:** Do not ship any TOP_M strategy. Do not treat this report as evidence that TOP_M works or fails.

---

## 19. Recommended Next Experiment

**Do not implement TOP_M yet.**

1. **Expand source material** (additional ops/policy docs) and re-embed, **or** carve a document-level holdout never used while authoring Dataset A.  
2. Build A/B meeting the minimum criteria in `step12b_primary_chunk_scope/DATASET_READINESS.md`.  
3. Only then implement TOP_M_1/2/3 under `step12b_primary_chunk_scope/`, freeze M from A, validate once on B.  
4. Keep production and frozen Step 8 guard unchanged until a held-out win is real.

---

*End of Step 12B. Stopped for review — no further optimization implemented.*
