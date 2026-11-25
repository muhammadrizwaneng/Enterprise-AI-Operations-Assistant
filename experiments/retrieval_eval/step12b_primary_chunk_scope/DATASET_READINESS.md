# Step 12B — Dataset Readiness Assessment

**Decision:** **STOP — do not run TOP_M ablation on the current six-document corpus.**  
**Date:** 2026-11-24  
**Mode:** Readiness gate only (no experimental strategy implemented; no ground truth invented)

---

## Requirement

Step 12B requires **two** independently verified datasets:

| Set | Role |
|---|---|
| Dataset A | Development — compare TOP_M_1 / TOP_M_2 / TOP_M_3; select one M |
| Dataset B | Fresh held-out — untouched until A’s candidate is frozen |

Both must cover:

1. Answerable from primary chunks  
2. Requiring neighboring chunks  
3. Lower-ranked irrelevant tables  
4. Lower-ranked irrelevant procedures  
5. Relevant tables in primary chunks  
6. Relevant procedures in primary chunks  
7. Genuinely incomplete evidence  
8. Distracting neighboring information  
9. Chunk-boundary evidence cases  

Ground truth must be verified from source text — not invented.

---

## Corpus inventory

| Document | Chunks |
|---|---:|
| customer_support_guidelines.md | 8 |
| delivery_policy.md | 7 |
| employee_handbook.md | 7 |
| privacy_policy.md | 8 |
| product_documentation.md | 8 |
| refund_policy.md | 8 |
| **Total** | **46 chunks (~21.3k chars)** |

Prior evaluation already consumed **Q1–Q47** (dev + H1 + H2) with **33/46** chunks used as primary evidence at least once.

---

## Independence failures

### 1. High-value facts already spent

Many natural TOP_M probe candidates **duplicate prior questions**, e.g.:

| Candidate fact | Already asked |
|---|---|
| PTO advance days | Q4 |
| Adult signature $1,000 | Q10 |
| Damage report 48 hours | Q11 |
| Physical refund 30 days | Q12 |
| Refund dispute $2,500 | Q16 |
| Data leak 1 hour | Q21 |
| OS patches 14 days | Q22 |
| privacy@ email | Q25 |

Paraphrasing these for “new” IDs would **not** be independent held-out material; it would leak prior evaluation topics into A/B.

### 2. Remaining verified atoms are too few for two full strata sets

After excluding already-covered topics, roughly **~15** distinct unused factual atoms remain (SKU format, eight categories, promo discount rule, inactive SKU rule, SI capacity notation, activation-key timing, three system roles, RMA recording, never-blame standard, legal bases, data-sharing parties, privacy ticket category `account`, in-stock processing 1–2 days, etc.).

Splitting ~15 atoms into **A and B**, each needing **nine** coverage types (including rare neighbor-gap / genuinely incomplete cases), leaves **insufficient non-overlapping items per stratum**.

### 3. Neighbor-needed / genuinely incomplete stratum is scarce

Live retrieval probes on remaining candidates found only **~2–3** primary-missing cases (e.g. system-roles chunk `#1` not in top-5; some multi-chunk privacy sharing).  

That is **not enough** to:

- Tune/select M on A using neighbor-needed failures, **and**  
- Validate the same risk on untouched B  

without recycling Q19-like material or inventing questions whose answers are not reliably grounded.

### 4. Ceiling / sufficiency blindness (historical)

Step 11 H2 already showed OFF ≈ 28 on most items while GENERAL still expanded. Building A/B from the same thin corpus risks **repeating ceiling effects**, so TOP_M “improvements” would be uninterpretable (Step 12A warned about this).

### 5. Same document pool ≠ independent source material

Even unused chunks sit in the **same six policies** already used to develop the frozen guard and prior ablations. True independence for a select-then-validate design needs either:

- Additional documents / denser policies, or  
- A pre-registered held-out document slice never used in A,  

neither of which exists in the current DB embeddings.

---

## What would be misleading if we proceeded anyway

- Claiming Dataset B is “fresh held-out” while recycling facts/topics from Q1–Q47  
- Selecting M on A when neighbor-needed n is tiny → unstable freeze  
- Reporting “TOP_M preserves necessary expansion” without adequate FN-skip test cases  
- Inventing or stretching ground truth to fill strata checkboxes  

Per Step 12B instructions: **stop rather than produce misleading conclusions.**

---

## Minimum readiness criteria (for a future retry)

Proceed with TOP_M ablation only when **all** hold:

1. **≥20** development + **≥20** held-out questions with **disjoint** answer facts (not paraphrases of Q1–Q47).  
2. Each of A and B has **≥5** items with offline-verified **primary missing from top-5** (neighbor-needed).  
3. Each has **≥5** items where top-1 is signal-clean but ranks 2–5 contain irrelevant table/procedure incompleteness (scope-sensitive).  
4. Each has **≥3** items where incompleteness is on the **answering** primary chunk (true cut table/procedure).  
5. Prefer **≥1 new source document** (or a frozen document holdout) not used while designing A.  
6. Non-ceiling scoring headroom: OFF mean not saturated near 28 on the majority of items.

---

## Allowed artifacts created

- This readiness note  
- Parent report `PRIMARY_CHUNK_SCOPE_ABLATION_REPORT.md` documenting the stop  

**Not created:** TOP_M guard code, A/B question sets with invented GT, eval runs, frozen M candidate.
