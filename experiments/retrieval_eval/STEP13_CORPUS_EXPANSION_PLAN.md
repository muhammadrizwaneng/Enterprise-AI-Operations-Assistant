# Step 13 — Evaluation Corpus Expansion Plan

**Mode:** READ-ONLY planning (no new documents, datasets, embeddings, experiments, or code changes)  
**Date:** 2026-11-24  
**Blocked experiment:** Step 12B TOP_M ablation (`PRIMARY_CHUNK_SCOPE_ABLATION_REPORT.md`, `step12b_primary_chunk_scope/DATASET_READINESS.md`)

---

## 1. Executive Summary

The current NovaForge evaluation corpus is **six short Markdown policies** (~17.3k source characters; **46** embedded chunks). Steps 5–11 already produced **47** grounded questions (Q1–Q47) that consume most high-value facts. Step 12B correctly stopped: two independent, strata-complete datasets cannot be built without inventing ground truth or recycling prior topics.

**Plan:** Expand the **source document set** first, then author **Dataset A (development)** and **Dataset B (held-out)** with verified GT, only then re-attempt Step 12B (TOP_M_1/2/3 vs BASELINE and OFF/BLIND/HYBRID_CAP2).

| Recommendation | Target |
|---|---|
| New documents | **8–12** additional ops/policy docs (see §5–6) |
| New independently verifiable fact atoms | **≥120** (preferably ≥150) |
| Development questions (A) | **≥24** (preferably 30) |
| Held-out questions (B) | **≥24** (preferably 30), frozen until A candidate selected |
| Neighbor-needed items | **≥5 per set** |
| Scope-sensitive distractor items | **≥5 per set** |

**Do not** create documents or datasets until this plan is approved.

---

## 2. Existing Corpus Audit

### 2.1 Source documents on disk

Path: `dataset/documents/`

| Document | Approx. chars | Headings (major topics) |
|---|---:|---|
| `customer_support_guidelines.md` | 3,018 | Mission, ticket categories, SLA table, required fields, status workflow, order-linked investigations, communication, escalation, close checklist |
| `delivery_policy.md` | 2,820 | Processing times, shipping methods, free shipping, status definitions, overdue, address changes, signature, damaged-in-transit |
| `employee_handbook.md` | 2,620 | Roles, hours, conduct, data handling, ticket expectations, PTO, equipment/VPN, acknowledgment |
| `privacy_policy.md` | 2,938 | Data collected, use, legal bases, sharing, retention table, security, rights, transfers, contacts |
| `product_documentation.md` | 2,978 | Catalog/SKU rules, stock, category guidance, warranty table, returns-by-type, diagnostics |
| `refund_policy.md` | 2,926 | Eligibility windows, order-status table, methods, non-refundable, partials, restocking, request steps, escalation |

**Total source text:** ~17.3k characters across **6** files.

### 2.2 Embedded retrieval units

| Document | Chunks |
|---|---:|
| customer_support_guidelines.md | 8 |
| delivery_policy.md | 7 |
| employee_handbook.md | 7 |
| privacy_policy.md | 8 |
| product_documentation.md | 8 |
| refund_policy.md | 8 |
| **Total** | **46** (~21.3k chars including chunk overlap) |

Windowing (~500-char) creates frequent truncation / cut-table / cut-list signals — useful for guard research, but **fact diversity** remains bounded by the six short sources.

### 2.3 Unique factual claim classes (illustrative inventory)

Not an exhaustive atom list; classes already densely mined:

- **Numeric thresholds:** free shipping $, flat shipping $, signature $1,000, damage 48h, refund windows, restocking %, dispute $2,500, SLA minutes/days, PTO 7 days, leak 1h, patch 14 days, stock reorder qty, backorder qty, freight 70 lb, warranties (12/24m), refund timings (3–5 / 5–10 days), acknowledge 4h, retention months, etc.
- **Status / table rows:** delivery statuses, refund eligibility by order status, ticket priorities, warranty by category, retention by data type.
- **Procedures:** overdue agent steps, refund request steps, escalation ladder, ticket status workflow, hardware replacement collection.
- **Contacts / negations:** privacy@, security@, no full PAN storage.
- **Roles / approvals:** Ops Manager overtime, backorder approval, finance escalation.

**Unused-as-primary chunks (13/46):** mostly title/overview stubs or partially overlapping continuations (`*#0`, roles mid-chunk, SKU/pricing, legal bases, order-status table `#2`, investigation steps `#5`). Step 12B estimated only **~15** remaining distinct atoms after excluding Q1–Q47 collisions.

---

## 3. Existing Evaluation Coverage

| Split | IDs | Role | n |
|---|---|---|---:|
| Dev | Q1–Q7 | Guard / hybrid development | 7 |
| H1 | Q8–Q27 | Step 9 held-out generalization | 20 |
| H2 | Q28–Q47 | Step 11 truncation ablation | 20 |
| **Total** | Q1–Q47 | | **47** |

**Primary-document load (refs):** support 15, delivery 13, refund 12, privacy 9, product 9, handbook 8.

**Evidence patterns already exercised:**

| Pattern | Examples |
|---|---|
| Single-chunk numerical / threshold | Q9–Q12, Q14, Q16, Q20–Q21, Q26, Q33–Q34, Q39–Q40, Q44 |
| Multi-chunk table | Q17, Q24, Q27, Q29–Q30, Q37, Q41 |
| Multi-chunk / neighbor completion | Q18–Q19, Q22, Q25 |
| Procedure / requirement phrasing | Q2, Q6–Q7, Q45–Q47 |
| Distraction under expansion | Q6 (restocking neighbor), Q19 (wrong hybrid neighbors), Q46 Blind |
| GENERAL any-hit over-trigger | Dominant on H1/H2 (Steps 10–12A) |
| Score ceiling | H2 HYBRID/OFF often 28/28 |

**33/46** chunks already appear as primary at least once.

---

## 4. Missing Evidence Scenarios

Gaps that the **current six docs cannot deeply support** (or cannot support *twice* for A and B):

1. **Order lifecycle ops** beyond shipping/refund snippets (place/cancel/edit line items, hold/release, split shipments).  
2. **Payment processing** (auth vs capture, chargebacks, net-30 credit memos as a full policy, failed payment retries) — only fragments today.  
3. **Inventory operations** (cycle count, quarantine, transfer between warehouses, allocation rules) — only reorder alert / backorder lines.  
4. **Account operations** (password reset, MFA, account merge, billing profile changes).  
5. **Finance operations** beyond refund escalation (credit notes, tax, invoice disputes, approval matrices).  
6. **Ticket management depth** (macros, CSAT, reopen windows, queue routing SLAs by channel).  
7. **Multi-document conflict / precedence** (which policy wins when delivery vs refund disagree) — almost absent.  
8. **Long procedures** spanning **≥3** chunks with a deliberate mid-list cut (rare; Q19-like gaps are scarce).  
9. **True negative retrieval** (question whose answer is *not* in corpus) — not used; optional for grounding tests, out of scope for TOP_M unless labeled separately.  
10. **Non-ceiling items** where OFF systematically misses facts without neighbors — under-supplied after Q1–Q47.

These gaps are why TOP_M cannot be stress-tested for **false skips** (neighbor-needed) and **true skips** (distractor-only incompleteness) on independent A/B sets.

---

## 5. Recommended New Document Categories

Candidate categories (not all mandatory). Prefer **new fact namespaces** that do not restate Q1–Q47 numbers.

| Priority | Category | Example doc (illustrative title only) | New retrieval challenges |
|---|---|---|---|
| **P0** | Order management | `order_management_sop.md` | Multi-step cancel/hold flows; status tables; chunk-boundary status lists |
| **P0** | Payment processing | `payment_processing_policy.md` | Auth/capture/chargeback timelines; method-specific tables; distractor finance tables |
| **P0** | Inventory operations | `inventory_operations_sop.md` | Quarantine/transfer procedures; qty thresholds; warehouse codes |
| **P1** | Account operations | `account_operations_guide.md` | Identity steps; ticket categories; contact paths ≠ privacy@ |
| **P1** | Finance / credit | `finance_credit_memo_policy.md` | Approval matrices; $ thresholds distinct from $2,500 refund dispute |
| **P1** | Ticket / queue management | `support_queue_routing.md` | Channel SLAs, reopen rules — distinct from existing priority SLA table |
| **P2** | Shipping ops (carrier-facing) | `carrier_exception_playbook.md` | Extends delivery without cloning free-shipping / 48h / $1,000 facts |
| **P2** | Returns logistics | `returns_warehouse_sop.md` | RMA QC steps beyond restocking % already used |
| **P2** | Security / access (ops) | `access_control_sop.md` | Distinct from handbook leak/patch atoms |
| **P3** | Vendor / procurement | `procurement_vendor_policy.md` | New actors; uncommon in prior Qs |

**Which categories unlock Step 12B strata:**

- **Distractor tables/procedures in lower ranks:** dense markdown tables + numbered SOPs in *new* docs that semantic search may retrieve beside an answering chunk from another doc.  
- **Neighbor-required:** deliberately place critical steps/rows in chunk *n+1* with wording that ranks chunk *n* or a sibling doc higher.  
- **Relevant primary tables/procedures:** answering evidence itself is a complete or cut table/list in rank 1–2.  
- **Independence:** new docs avoid paraphrasing existing thresholds (30 days, 70 lb, 24 months monitors, etc.).

**Do not** “expand” by only lengthening the existing six files with the same facts — that still leaks topics into A/B and contaminates historical comparisons.

---

## 6. Recommended Corpus Size

### 6.1 Documents and facts

| Item | Minimum | Preferred |
|---|---:|---:|
| Additional new documents | **8** | **10–12** |
| Typical length per new doc | ~2.5–4.5k chars | similar density to current policies |
| New verifiable fact atoms (numeric, named entity, hard constraint, step lists) | **≥120** | **≥150** |
| Embedded chunks after re-ingest (new docs only) | ~60+ | ~80–100 |

Rationale: Step 12B needs **two** sets × **9** strata with multiples per stratum, plus non-ceiling items. ~15 leftover atoms failed; **≥120** new atoms gives headroom after discarding weak/unretrievable probes.

### 6.2 Questions

| Set | Minimum n | Preferred n |
|---|---:|---:|
| Dataset A (development) | 24 | 30 |
| Dataset B (held-out) | 24 | 30 |
| **Total new questions** | **48** | **60** |

### 6.3 Per-evidence-category minima (**each** of A and B)

| Category | Min questions / set |
|---|---:|
| Primary-chunk-sufficient (OFF should succeed) | 8 |
| Neighbor-required (primary continuation missing from top-5 **or** fact only in neighbor) | 5 |
| Lower-rank irrelevant **table** drives incompleteness; answer already in top-M | 3 |
| Lower-rank irrelevant **procedure** drives incompleteness; answer already in top-M | 3 |
| Relevant table in primary / top ranks | 3 |
| Relevant procedure in primary / top ranks | 3 |
| Chunk-boundary cut (answer straddles adjacent chunks) | 3 |
| Genuinely incomplete in top-5 without expansion (labeled expect expand) | 3 |
| Distracting neighbor under Blind/Hybrid (harm risk) | 2 |

Categories may overlap on one question (e.g. neighbor-required + chunk-boundary); count explicitly in a stratum matrix — do not double-count toward the **n≥24** floor without meeting each minimum.

### 6.4 Limitations of small datasets

- **n≈7–20** (historical) made strategy rankings **question-dominated** (e.g. Q6, Q19).  
- Ceiling scores hide expansion harm/benefit.  
- Bootstrap CIs on n=20 are exploratory only.  
- Single-doc pools cannot separate **document leakage** from **method** gains.  
- Selecting M on A with &lt;5 neighbor-needed items yields an unstable freeze.

---

## 7. Development Dataset Design

**Name:** Dataset A (e.g. future Q48+ block; exact IDs assigned only after corpus exists).

**Purpose:** Compare BASELINE vs TOP_M_1/2/3 (plus OFF/BLIND/HYBRID_CAP2) under matched seeds; **select one M**.

**Construction rules:**

1. Author questions **only** from **new** documents (or explicitly reserved new sections never used in B).  
2. After draft, run retrieval probes (top-5) and record rank-wise table/proc/trunc flags — **offline**, not fed to the guard.  
3. Keep A’s stratum matrix filled to §6.3 minima.  
4. Prefer non-ceiling items: at least **40%** of A with expected OFF total ≤ 24 under the existing rubric family (or documented harder checklist).  
5. **No peeking at B**; B IDs/questions sealed.

**Outputs (future):** `dataset_a.py`, `dataset_a_answer_key.py`, stratum annotations, retrieval probe JSON.

---

## 8. Held-Out Dataset Design

**Name:** Dataset B.

**Purpose:** Single frozen evaluation of the **A-selected** TOP_M candidate vs BASELINE and baselines.

**Construction rules:**

1. Same category minima as A (§6.3).  
2. **Disjoint fact atoms** from A (see §10).  
3. Prefer **document-level holdout**: e.g. 3–4 new docs used only in B, never inspected while tuning prompts/thresholds on A.  
4. Written **before** looking at A’s TOP_M score deltas (ideal) or at least sealed before freeze.  
5. Same scoring rubric family as A for comparability; do not retune rubric using B outcomes.

**Outputs (future):** `dataset_b.py`, `dataset_b_answer_key.py`, sealed until freeze.

---

## 9. Ground-Truth Verification Method

Every question record **must** include (offline only):

| Field | Requirement |
|---|---|
| `expected_answer` / fact checklist | Verbatim-supported claims |
| `source_document` | File name in corpus |
| `source_section` | Heading path |
| `primary_chunks` | Chunk indices after embedding |
| `evidence_completeness` | `sufficient_in_top5` / `needs_neighbor` / `insufficient_even_with_neighbors` |
| `neighbor_necessary` | bool + justification tied to retrieval probe |
| `stratum_tags` | Multi-label from §6.3 |
| `verification` | Quote or exact substring(s) from source **before** embedding |

**Process:**

1. Write fact from **source Markdown** (not from model output).  
2. After ingest/embed, confirm primary chunk text still contains the substring.  
3. Run retrieval probe; if primary missing, classify neighbor-needed or revise question wording **without** peeking at guard decisions for tuning on B.  
4. Dual-check: second pass (human or separate checklist) that answer key needles appear in cited chunks.

**Forbidden:** LLM-authored “facts” not present in documents; copying Q1–Q47 keys with paraphrased stems; labeling `neighbor_necessary=True` without a failed top-5 primary probe.

---

## 10. Dataset Independence Rules

| Risk | Prevention |
|---|---|
| Duplicate questions | Canonical fact ID registry (`fact_id` → doc/section/value); reject new Q if fact_id used |
| Paraphrased duplicates | Same registry keyed by **normalized fact**, not by question text |
| Fact leakage A↔B | Partition fact_ids before writing stems; no shared atoms |
| Document leakage | Hold out ≥3 new docs exclusively for B; authors of A do not read B docs |
| Ground-truth leakage into guard | Answer keys / stratum labels imported only by scorers; never by TOP_M / evidence_guard |
| Dev/validation contamination | Freeze M using **only** A metrics; touch B once; no threshold edits after B reveal |
| Historical contamination | Do not reuse Q1–Q47 facts; do not fine-tune on H1/H2 for TOP_M |
| Embedding leakage | Re-embed new docs in controlled ingest; do not edit old six docs’ factual content in place for “new” atoms |

**Registry fields (planned):** `fact_id`, `doc`, `section`, `canonical_value`, `split` ∈ {A,B,blocked_legacy}.

Legacy Q1–Q47 facts → `blocked_legacy`.

---

## 11. Statistical Evaluation Requirements

When Step 12B is eventually run on the expanded corpus:

| Requirement | Spec |
|---|---|
| Seeds | 5 matched seeds (e.g. 101–505) if framework supports |
| Configs | OFF, BLIND, HYBRID_CAP2, BASELINE, TOP_M_1, TOP_M_2, TOP_M_3 |
| Primary metrics | Mean/per-q total, variance, paired Δ, bootstrap 95% CI |
| Guard metrics | Skip rate, unnecessary expansion rate (offline oracle), FN expand-fail on neighbor-needed |
| Context | Chars, neighbor counts |
| Rubric dims | Completeness, correctness, unsupported claims (existing 7-metric family) |
| Selection rule (A) | Pre-register: e.g. maximize mean on A subject to neighbor-needed mean ≥ OFF−ε and skip-rate constraints |
| Validation (B) | Report A-selected M only; treat other M on B as exploratory or omit |
| Reporting | Separate A vs B; do not pool to “pick winner” after B |

Small-n caveat remains until n≥24 per set; still prefer stratum-wise tables over a single mean.

---

## 12. Step 12B Readiness Criteria

Re-open Step 12B **only when all** are true:

1. **≥8** new documents ingested and embedded; old six unchanged in factual content.  
2. Fact registry lists **≥120** new atoms; Q1–Q47 marked blocked.  
3. Dataset A and B each have **≥24** questions with verified GT and §6.3 minima met.  
4. Document holdout for B documented.  
5. Retrieval probe JSON shows ≥5 neighbor-needed and ≥5 top-M-sensitive distractor items **per set**.  
6. Scoring harness extended under `step12b_primary_chunk_scope/` without modifying frozen `evidence_guard.py` (TOP_M wrapper only).  
7. Written freeze rule for selecting M from A before B unlock.  
8. Sign-off on this plan’s execution phase.

Until then, TOP_M results would be **not trustworthy**.

---

## 13. Risks and Limitations

| Risk | Mitigation |
|---|---|
| New docs accidentally restate old thresholds | Fact registry + review checklist |
| Embedding/chunking changes alter historical comparability | Keep old docs frozen; report new-corpus results as new regime |
| Authors bias A toward TOP_M success | Pre-register strata; include FN-risk neighbor items |
| Still too few hard negatives | Prefer longer SOPs with intentional boundary cuts |
| Synthetic-looking policies | Prefer realistic ops detail; still must be **authored as source of truth**, then verified — never reverse-engineer GT from model answers |
| Scope creep into production RAG | Keep all work under `experiments/` until explicit ship decision |
| Plan over-prescribes doc titles | Treat §5 titles as examples; categories matter more than names |

---

## 14. Recommended Next Action

**Await approval**, then in order:

1. **Author** 8–12 new Markdown sources under a new directory (e.g. `dataset/documents_v2/` or additive files) — **after** approval only.  
2. **Ingest/embed** via existing pipeline; do not alter production prompts/guard.  
3. Build **fact registry** and seal B document holdout.  
4. Author **Dataset A** + answer keys; fill stratum matrix; run retrieval probes.  
5. Author **Dataset B** + keys without using A outcomes.  
6. Implement **TOP_M scope wrappers** only under `experiments/retrieval_eval/step12b_primary_chunk_scope/`.  
7. Run A → freeze M → run B → write a new empirical Step 12B report (replace the readiness-stop narrative with measured results).

**This Step 13 deliverable stops here.** No documents created. No datasets authored. No experiments run.

---

*End of Step 13 planning report. Waiting for approval before corpus authoring.*
