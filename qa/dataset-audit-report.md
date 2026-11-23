# Dataset & Database Quality Audit Report

**Project:** Enterprise AI Operations Assistant  
**Audit date (UTC):** 2026-11-23  
**Database:** `enterprise_ai` @ `localhost:5432`  
**Scope:** PostgreSQL data, CSV exports, RAG documents, core API endpoints  
**Data modification:** None — no safe consistency defects required repair

---

## Overall summary

| Metric | Result |
|---|---|
| Checks executed | 15 |
| **PASS** | **15** |
| **FAIL** | **0** |
| Total DB records | 9,217 |
| Data fixes applied | 0 |
| Overall quality | **Excellent — production-ready synthetic foundation** |

All required integrity rules passed: schema presence, primary keys, foreign keys, unique natural keys, order financial consistency, payment linkage/logic, ticket assignment integrity, required-field NULLs, status distributions, CSV↔DB parity, RAG document completeness, and API health/stats endpoints.

**Advisory (not failures):** 173 orders have no payment row. This is expected by design (payments target 1,800–2,000 for 2,000 orders) and represents unpaid/pending checkout states.

---

## Table inventory

| Table | DB rows | CSV rows | Match |
|---|---:|---:|---|
| roles | 3 | 3 | Yes |
| users | 20 | 20 | Yes |
| customers | 500 | 500 | Yes |
| products | 100 | 100 | Yes |
| orders | 2,000 | 2,000 | Yes |
| order_items | 4,267 | 4,267 | Yes |
| payments | 1,827 | 1,827 | Yes |
| support_tickets | 500 | 500 | Yes |
| **Total** | **9,217** | **9,217** | **Yes** |

---

## Check results

### 1. All 8 database tables exist

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 8 expected tables |
| **Issues found** | None |
| **Recommended fixes** | None |

**Present:** `roles`, `users`, `customers`, `products`, `orders`, `order_items`, `payments`, `support_tickets`

---

### 2. Primary keys unique and non-null

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 9,217 rows across 8 tables |
| **Issues found** | None |
| **Recommended fixes** | None |

For every table: `id IS NULL` count = 0 and `COUNT(DISTINCT id) = COUNT(*)`.

---

### 3. Foreign keys reference existing records

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 13,881 FK evaluations (sum of child-table rows across FK checks) |
| **Issues found** | None |
| **Recommended fixes** | None |

| Relationship | Orphan count |
|---|---:|
| `users.role_id` → `roles.id` | 0 |
| `orders.customer_id` → `customers.id` | 0 |
| `order_items.order_id` → `orders.id` | 0 |
| `order_items.product_id` → `products.id` | 0 |
| `payments.order_id` → `orders.id` | 0 |
| `support_tickets.customer_id` → `customers.id` | 0 |
| `support_tickets.order_id` → `orders.id` (when not NULL) | 0 |
| `support_tickets.assigned_to` → `users.id` (when not NULL) | 0 |

---

### 4. No duplicate emails, SKUs, or order numbers

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 4,950 rows across unique-key tables |
| **Issues found** | None |
| **Recommended fixes** | None |

Verified unique:

- `customers.email`
- `users.email`
- `products.sku`
- `orders.order_number`
- Also verified: `payments.payment_reference`, `support_tickets.ticket_number`, `roles.name`

---

### 5. Every order total matches the sum of its order items

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 2,000 orders (+ related 4,267 order items) |
| **Issues found** | None |
| **Recommended fixes** | None |

Integrity rules verified:

1. Every order has ≥ 1 order item  
2. `SUM(order_items.line_total) = orders.subtotal`  
3. `orders.subtotal + tax_amount + shipping_amount = orders.total_amount`  
4. `ROUND(unit_price * quantity, 2) = line_total` for all items (0 mismatches)

---

### 6. Every payment references a valid order

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 1,827 payments |
| **Issues found** | None |
| **Recommended fixes** | None |

---

### 7. Payment amounts and statuses are logically consistent

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 1,827 payments |
| **Issues found** | None |
| **Recommended fixes** | None |

Additional logic checks (all clean):

- No NULL / non-positive amounts  
- No unexpected payment statuses  
- Completed / refunded / partially_refunded always have `paid_at`  
- Pending / failed never have `paid_at`  
- Completed payment amounts match linked `orders.total_amount`  
- No cancelled orders with `completed` payments  

**Payment status distribution**

| Status | Count |
|---|---:|
| completed | 776 |
| refunded | 308 |
| partially_refunded | 271 |
| failed | 243 |
| pending | 229 |

**Payment method distribution**

| Method | Count |
|---|---:|
| invoice | 381 |
| paypal | 374 |
| credit_card | 363 |
| debit_card | 357 |
| bank_transfer | 352 |

---

### 8. Support ticket assignments reference valid users

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 500 tickets |
| **Issues found** | None |
| **Recommended fixes** | None |

- 0 tickets assigned to missing users  
- 0 tickets assigned to inactive users  
- 61 tickets intentionally unassigned (`assigned_to IS NULL`)

---

### 9. NULL values in important fields

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 24 required-field probes |
| **Issues found** | None |
| **Recommended fixes** | None |

Required fields (email, names, SKUs, statuses, amounts, FKs, quantities, subjects, priorities) all non-null / non-empty where required.

**Expected optional NULLs (informational)**

| Field | NULL count |
|---|---:|
| `customers.company_name` | 169 |
| `orders.shipped_date` | 831 |
| `orders.delivered_date` | 1,299 |
| `orders.notes` | 1,399 |
| `payments.paid_at` | 472 |
| `support_tickets.order_id` | 178 |
| `support_tickets.assigned_to` | 61 |
| `support_tickets.resolved_at` | 297 |

These NULL patterns are business-valid (not every order is shipped/delivered; not every ticket is order-linked or resolved).

---

### 10. Order, payment, ticket, and customer status distributions

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 4,827 rows (orders + payments + tickets + customers) |
| **Issues found** | None |
| **Recommended fixes** | None |

**Order statuses** (includes required edge cases)

| Status | Count |
|---|---:|
| delivered | 587 |
| shipped | 338 |
| processing | 284 |
| confirmed | 258 |
| cancelled | 153 |
| pending | 136 |
| overdue | 130 |
| returned | 114 |

**Ticket statuses**

| Status | Count |
|---|---:|
| waiting_customer | 108 |
| resolved | 107 |
| closed | 96 |
| in_progress | 95 |
| open | 94 |

**Ticket priorities**

| Priority | Count |
|---|---:|
| medium | 238 |
| low | 122 |
| high | 102 |
| urgent | 38 |

**Customer / user activity**

| Entity | Active | Inactive |
|---|---:|---:|
| customers | 462 | 38 |
| users | 18 | 2 |

---

### 11. Generated CSV files match database records

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 18,434 ID comparisons (CSV + DB) |
| **Issues found** | None |
| **Recommended fixes** | None |

For every table:

- CSV row count == DB row count  
- CSV `id` set == DB `id` set (no extras either side)

CSV location: `dataset/csv/*.csv`

---

### 12. RAG documents exist and contain meaningful content

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 6 documents |
| **Issues found** | None |
| **Recommended fixes** | None |

| Document | Words | Headings | Size (bytes) |
|---|---:|---:|---:|
| `refund_policy.md` | 462 | 10 | 2,936 |
| `delivery_policy.md` | 407 | 10 | 2,826 |
| `employee_handbook.md` | 380 | 10 | 2,632 |
| `product_documentation.md` | 430 | 16 | 2,978 |
| `customer_support_guidelines.md` | 473 | 10 | 3,028 |
| `privacy_policy.md` | 438 | 15 | 2,938 |

All documents exist under `dataset/documents/`, exceed the minimum content threshold (≥100 words, ≥3 headings), and include structured business-policy content suitable for later RAG ingestion.

---

## API endpoint tests

### GET `/`

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 1 response |
| **Issues found** | None |
| **Recommended fixes** | None |

HTTP 200 — returns welcome payload including `db_browser`, `docs`, and `health` links.

### GET `/health`

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 1 response |
| **Issues found** | None |
| **Recommended fixes** | None |

HTTP 200 — `status=ok`, app name and environment present.

### GET `/api/v1/database/stats`

| Field | Value |
|---|---|
| **Status** | **PASS** |
| **Records checked** | 1 response (+ cross-check vs DB counts) |
| **Issues found** | None |
| **Recommended fixes** | None |

HTTP 200 — payload exactly matches live DB counts (`total_records=9217`).

---

## Fixes applied

None.

No safe consistency defects were found. Existing synthetic data was **not** regenerated, deleted, or overwritten.

---

## Overall dataset quality summary

The Enterprise AI Operations Assistant foundation dataset is **internally consistent and audit-clean**.

**Strengths**

- Complete 8-table schema with valid UUID primary keys  
- Zero orphan foreign keys  
- Unique emails / SKUs / order numbers / payment & ticket references  
- Exact order financial arithmetic (items → subtotal → total)  
- Payment and ticket assignment logic holds under stricter consistency probes  
- Realistic multi-status distributions including cancelled, returned, overdue, pending  
- CSV exports are a perfect mirror of PostgreSQL contents  
- Six RAG policy documents are present and substantive  
- Core FastAPI endpoints are healthy and stats-accurate  

**Residual notes (non-blocking)**

- 173 orders intentionally lack payments (within the designed 1,800–2,000 payment range)  
- Optional NULLs on shipping/delivery dates, notes, ticket order links, and unresolved tickets are expected  

**Verdict:** Dataset quality is suitable for the next project stage (API enrichment / RAG / agents) without a data cleanup pass.
