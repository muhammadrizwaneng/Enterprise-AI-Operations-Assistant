# Excluded Legacy Topics (Q1–Q47)

These topics/facts from the **legacy six-document corpus** and evaluation questions **must not** be reused in future Dataset A/B built on corpus v2.

Semantic paraphrases of the same numeric thresholds, contacts, SLAs, and procedures are also excluded.

## Document sources (legacy only)

`dataset/documents/`: delivery_policy, refund_policy, customer_support_guidelines, employee_handbook, privacy_policy, product_documentation.

## Blocked fact themes (by legacy Q)

| Legacy Q | Blocked theme / canonical values |
|---|---|
| Q1 | Delivery transit times by shipping method (standard/expedited/etc. table) |
| Q2 / Q46 | Overdue package agent steps; **7 calendar days** lost-package replace/refund |
| Q3 | Late delivery refund eligibility tied to overdue/lost rules |
| Q4 | PTO notice **7 days** |
| Q5 | How to contact support / ticket category listing as intake answer |
| Q6 / Q45 | Defect evidence (photo/ticket); monitor **ISO 9241-307 Class II** |
| Q7 | Consumer refund request steps (open ticket `refund_request`, RMA…) |
| Q8 | Free shipping merchandise threshold **$150** |
| Q9 | Flat shipping **$9.99** below threshold |
| Q10 | Adult signature above **$1,000** |
| Q11 | Visible damage report within **48 hours** (+ photos) |
| Q12 | Physical refund window **30 calendar days** |
| Q13 | Software/digital refund **14 calendar days** / not activated |
| Q14 | Restocking fee **15%** |
| Q15 | Non-refundable item list (custom hardware, consumables, services, final sale) |
| Q16 | Urgent refund dispute escalate above **$2,500** to Operations Manager |
| Q17 | Medium priority first response **4 business hours** |
| Q18 / Q47 | Escalation path Agent → Senior/Lead → Ops Manager → Finance → Admin/Security |
| Q19 / Q32 | Ticket statuses open/in_progress/waiting_customer/resolved/closed; no open→closed without resolution note |
| Q20 | Collaboration hours **10:00–16:00** |
| Q21 | Data leak report within **1 hour** |
| Q22 | OS patches within **14 days** (VPN/production) |
| Q23 | Orders & invoices retention **7 years** |
| Q24 | Support tickets retention **3 years** after closure |
| Q25 | `privacy@novaforge.example` |
| Q26 | Reorder alert at **10 units** |
| Q27 | Laptop warranty **12 months** |
| Q28 | Address changes only before shipping label |
| Q29 | Urgent first response **30 minutes** |
| Q30 | High priority resolution **1 business day** |
| Q31 | Required ticket fields (customer reference, subject, category, …) |
| Q33 | Card refunds **3–5 business days** |
| Q34 | Bank transfer refunds **5–10 business days** |
| Q35 | Shipping cost refunded if entire order returned / NovaForge error |
| Q36 | `security@novaforge.example` |
| Q37 | Security logs retention **12 months** |
| Q38 | Does not store full payment card numbers |
| Q39 | Backorders above **50 units** need Ops Manager |
| Q40 | Freight appointments over **70 lb** |
| Q41 | Monitor warranty **24 months** |
| Q42 | Hardware replacement collection (SKU, serial, order number, …) |
| Q43 | Overtime pre-approved by Operations Manager |
| Q44 | Acknowledge tickets within **4 business hours** |

## Email / contact strings blocked for A/B answers

- `privacy@novaforge.example`
- `security@novaforge.example`

(New corpus uses different functional mailboxes such as `orders@`, `payments@`, `accounts@`, etc.)

## Overlap notes vs corpus v2

| Potential collision | How corpus v2 avoids it |
|---|---|
| Refund timing / eligibility | Credit memos & warehouse RMA grading — not consumer 30-day / 15% restock |
| Shipping $ / signature / 48h damage | Carrier exception codes, intercept fees, replacement value matrix — different numbers |
| Support priority SLAs / escalation ladder | Channel queues, reopen windows, CSAT — not priority minute/day table |
| Inventory reorder 10 units / backorder 50 | Safety floors, ABC cycle counts, allocation priority % — new metrics |
| Warranty months / ISO pixel | Not present in v2 docs |
| Leak 1h / patch 14d | Access control joiner/leaver/JIT — different timers |
| PAN non-storage | Not restated; payment doc defers to Privacy Policy without repeating the claim |

## Rule for Dataset A/B authors

If a draft question’s correct answer equals a blocked canonical value or is a paraphrase of a blocked theme, **reject** and pick a `FACT_REGISTRY.md` atom instead.
