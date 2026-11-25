# Finance Credit Memo Policy

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** FIN-CRD-520  
**Effective Date:** May 2, 2026  
**Last Updated:** November 10, 2026  
**Owner:** Revenue Accounting

---

## 1. Purpose

Governs issuance, approval, aging, and application of credit memos (CM) for invoice customers. Separate from card/ACH refund capture timing in Payment Processing Policy and from consumer refund eligibility windows in Refund Policy.

## 2. Credit Memo Types

| Type code | Use case | Posts to |
|---|---|---|
| `CM-PRICE` | Pricing error on billed lines | Accounts receivable |
| `CM-QTY` | Short shipment accepted by customer | Accounts receivable |
| `CM-SVC` | Service credit goodwill | Contra-revenue |
| `CM-TAX` | Tax correction | Tax payable clearing |
| `CM-SLA` | Contractual SLA credit | Contra-revenue |

## 3. Approval Matrix

| CM amount (USD) | Approver | Second approver |
|---|---|---|
| ≤ 250.00 | Billing Specialist | None |
| 250.01 – 1,500.00 | Billing Supervisor | None |
| 1,500.01 – 8,000.00 | Finance Manager | Billing Supervisor |
| 8,000.01 – 25,000.00 | Controller | Finance Manager |
| Above 25,000.00 | CFO delegate | Controller |

Self-approval is prohibited. The requester and approver must be different user IDs.

## 4. Issuance Procedure

1. Open ticket category `credit_memo` with invoice number and type code.
2. Attach calculation worksheet showing original vs corrected extended amounts.
3. Obtain approvals per matrix before posting.
4. Post CM in ERP within **1 business day** of final approval.
5. Email CM PDF to the billing contact on file within **4 business hours** of posting.

## 5. Aging and Application

- Open CMs auto-apply to the next invoice for the same account unless flagged `manual_apply`.
- Unapplied CMs older than **60 calendar days** appear on the weekly AR exception report.
- CMs older than **180 calendar days** require Controller review for write-off vs refund conversion.
- Conversion of CM to original-method refund needs Payment Ops ticket linkage.

## 6. SLA Credits

`CM-SLA` requires:

- Contract clause citation
- Incident ID from Service Desk
- Downtime minutes ≥ **45** in a calendar month **or** missed commitment count ≥ **3**

Maximum `CM-SLA` per account per quarter: **12%** of that quarter’s billed recurring fees.

## 7. Documentation Retention

Credit memo packets (ticket, worksheet, approvals, PDF) are retained **5 years** in the finance archive bucket `fin-cm-archive`.

## 8. Contacts

AR desk: `creditmemos@novaforge.example`  
Controller queue: `#fin-controller`
