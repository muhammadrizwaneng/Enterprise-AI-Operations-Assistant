# Step 13A — Corpus Authoring Report

**Date:** 2026-11-24  
**Mode:** Authoring only (no ingest/embeddings, no Dataset A/B, no TOP_M, no production changes)  
**Corpus root:** `experiments/retrieval_eval/corpus_v2/`

---

## Overall verdict: **PASS WITH ISSUES**

Corpus v2 meets the quantitative gates (11 documents, **217** verified fact atoms, exclusion list, registry traceability, no blocked legacy needles in sources). Minor issues remain around a few short evidence substrings and the fact that documents are not yet embedded for retrieval probing.

Ready for **Dataset A/B construction planning/authoring** after review — **not** ready to re-run Step 12B until A/B exist and docs are ingested.

---

## 1. Documents created and topics

All under `corpus_v2/documents/`. Fictional **NovaForge** evaluation content; **not** real SeeBiz production policy (`corpus_v2/README.md`).

| # | Document | Topic |
|---|---|---|
| 1 | `order_management_sop.md` | Order states, edits, holds, splits, cancellation |
| 2 | `payment_processing_policy.md` | Auth/capture, failures, settlement, chargebacks |
| 3 | `inventory_operations_sop.md` | Buckets, cycle counts, quarantine, transfers, allocation |
| 4 | `account_operations_guide.md` | Tiers, reset/MFA, profile, merge, closure |
| 5 | `finance_credit_memo_policy.md` | CM types, approvals, aging, SLA credits |
| 6 | `support_queue_routing.md` | Channels, skills, reopen, CSAT, broadcast |
| 7 | `carrier_exception_playbook.md` | Carrier EX codes, intercept, NSR ladder, intl |
| 8 | `returns_warehouse_sop.md` | RMA dock grading, refurb/scrap, keep-item |
| 9 | `access_control_sop.md` | Joiner/mover/leaver, JIT, vendor access |
| 10 | `procurement_vendor_policy.md` | Vendor tiers, PO/ASN, scorecards, PIP |
| 11 | `platform_uptime_sla.md` | Availability, SEV, maintenance, error budget |

**Count:** 11 (within required 8–12).

Legacy six files under `dataset/documents/` were **not** modified.

---

## 2. Fact atom count per document

From `FACT_REGISTRY.md`:

| Document | Fact count |
|---|---:|
| `order_management_sop.md` | 19 |
| `payment_processing_policy.md` | 23 |
| `inventory_operations_sop.md` | 24 |
| `account_operations_guide.md` | 21 |
| `finance_credit_memo_policy.md` | 19 |
| `support_queue_routing.md` | 18 |
| `carrier_exception_playbook.md` | 17 |
| `returns_warehouse_sop.md` | 17 |
| `access_control_sop.md` | 18 |
| `procurement_vendor_policy.md` | 20 |
| `platform_uptime_sla.md` | 21 |
| **Total** | **217** |

---

## 3. Total distinct fact atoms

**217** unique fact IDs (gate ≥120: **PASS**).

---

## 4. Fact registry structure

File: `experiments/retrieval_eval/corpus_v2/FACT_REGISTRY.md`

| Column | Content |
|---|---|
| Fact ID | e.g. `F-ORD-001`, `F-PAY-017` |
| Source document | Filename in `documents/` |
| Section | Markdown heading |
| Supporting evidence | Exact substring verified present in file |
| Normalized fact | Testable claim |
| Topic | Coarse tag |
| Testable | Yes/No |
| Related | Optional cross-links |

Validation: automated substring check → **0 missing evidence** after authoring fixes.

---

## 5. Legacy topic exclusion results

File: `experiments/retrieval_eval/corpus_v2/EXCLUDED_LEGACY_TOPICS.md`

- Lists Q1–Q47 blocked themes and canonical values.
- Scan of all 11 v2 documents for blocked needles (`$150`, `$9.99`, `$1,000`, `48 hours`, `30 calendar days`, `14 calendar days`, `15%`, `$2,500`, `30 minutes`, `7 calendar days`, `10 units`, `50 units`, `70 lb`, `12 months`, `24 months`, `ISO 9241`, `privacy@` / `security@`, collaboration hours, etc.): **all CLEAN**.
- Where draft text initially collided (e.g. `7 calendar days` auth TTL, `24 months` vendor audit, `15%` allocation cap, `30 minutes` timers, `48 hours` MW notice), values were **rewritten** to new numbers/topics.

---

## 6. Contradiction and overlap checks

| Check | Result |
|---|---|
| Internal cross-refs (orders↔payments↔carrier↔returns; CM-SLA↔platform SLA) | Consistent roles/mailboxes |
| Duplicate fact IDs | None |
| Overlap with Q1–Q47 canonical values | None found in blocked-needle scan |
| Semantic near-duplicates across v2 docs | Low; shared concepts (e.g. `sla_critical`) intentionally cross-linked, not conflicting |

No contradictions requiring document edits were found.

---

## 7. Source traceability results

- Every registry row cites document + section + evidence substring.  
- Evidence presence: **217/217 verified**.  
- **Issue (minor):** a minority of evidence strings are short (e.g. isolated durations) and could match more than one sentence in-file; still present and section-scoped. Prefer longer unique quotes when authoring Dataset A/B keys.

---

## 8. Gaps / failed validation gates

| Gate | Status |
|---|---|
| 8–12 new documents | **PASS** (11) |
| ≥120 fact atoms | **PASS** (217) |
| Every fact has source + section | **PASS** |
| Facts sufficiently independent for future Qs | **PASS** (with minor short-evidence note) |
| No accidental Q1–Q47 fact reuse in sources | **PASS** (needle scan clean) |
| Enough detail for future question construction | **PASS** (tables + procedures + thresholds) |
| No contradictions between new docs | **PASS** |
| Each document independently hold-out-able for A/B | **PASS** (standalone files; holdout assignment deferred) |
| Embedded in vector DB / retrieval probed | **NOT DONE** (out of scope for 13A) |
| Dataset A/B created | **NOT DONE** (explicitly deferred) |

---

## 9. Ready for Dataset A/B construction?

**Yes, conditionally — PASS WITH ISSUES.**

Authors may begin Dataset A/B design against `FACT_REGISTRY.md` and `EXCLUDED_LEGACY_TOPICS.md`, subject to review approval.

Still required before Step 12B empirical rerun:

1. Approve corpus v2 content.  
2. Ingest/embed v2 documents (without altering legacy six).  
3. Author sealed Dataset A and Dataset B with stratum minima from Step 13 plan.  
4. Only then implement TOP_M under `step12b_primary_chunk_scope/`.

---

## Files created (allowed paths only)

```
experiments/retrieval_eval/corpus_v2/README.md
experiments/retrieval_eval/corpus_v2/FACT_REGISTRY.md
experiments/retrieval_eval/corpus_v2/EXCLUDED_LEGACY_TOPICS.md
experiments/retrieval_eval/corpus_v2/documents/*.md  (11 files)
experiments/retrieval_eval/STEP13A_CORPUS_AUTHORING_REPORT.md
```

**Stopped for review.** No Dataset A/B, no embeddings, no TOP_M, no Step 12B execution.
