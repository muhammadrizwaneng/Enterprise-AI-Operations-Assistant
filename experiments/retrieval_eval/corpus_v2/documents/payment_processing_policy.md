# Payment Processing Policy

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** FIN-PAY-210  
**Effective Date:** February 12, 2026  
**Last Updated:** November 18, 2026  
**Owner:** Treasury & Billing Systems

---

## 1. Scope

Covers authorization, capture, settlement, failed payments, and chargeback intake for storefront and invoice channels. Card-number storage rules in Privacy Policy still apply; this document adds operational payment timelines.

## 2. Authorization and Capture

| Channel | Authorize when | Capture when | Auth hold TTL |
|---|---|---|---|
| Card (online) | Checkout submit | On `allocated` or 18 hours after auth, whichever first | 8 calendar days |
| Card (phone) | Agent confirms cart | Same business day as auth | 5 calendar days |
| ACH debit | Checkout submit | After `packed` | 3 business days to return window |
| Net-30 invoice | Order `authorized` | Per invoice due date | N/A |
| Wallet | Checkout submit | On `labeled` | 10 calendar days |

Manual capture before allocation requires Billing Supervisor approval code `CAP-EARLY`.

## 3. Failed Payment Handling

1. Soft declines: retry automatically at **T+2 hours** and **T+26 hours**.
2. Hard declines: mark order `PAYMENT_RETRY` hold and email the payer within **45 minutes**.
3. After **3** failed capture attempts, cancel unshipped lines and release inventory.
4. Agents must not re-run capture more than once per clock hour without supervisor override.

## 4. Settlement Batches

- Card settlement files generate at **22:00 UTC** daily.
- ACH settlement files generate at **14:00 UTC** on banking days only.
- Unmatched settlement rows older than **36 hours** open a Finance queue ticket category `settle_mismatch`.

## 5. Chargebacks

| Stage | Owner | Response deadline |
|---|---|---|
| Inquiry received | Billing Specialist | 2 business days |
| Soft chargeback | Billing Specialist | 5 business days |
| Hard chargeback | Billing Supervisor | 7 business days |
| Pre-arbitration | Treasury Lead | 3 business days |

Evidence packs must include order timeline PDF, shipment proof, and customer communications export. Minimum pack size is **3** attachments.

Chargebacks above **$4,000.00** require Treasury Lead acknowledgment within **4 business hours** of intake.

## 6. Credits vs Refunds

- Merchant credits (store credit) post within **1 business day** of approval.
- Original-method refunds follow Refund Policy timing; this policy only governs capture reversal initiation, which must start within **2 business hours** of refund approval.
- Partial capture reversals are allowed down to a **$1.00** residual authorization floor.

## 7. Prohibited Actions

- Splitting one customer charge into more than **4** separate captures for the same order.
- Capturing payment for SKUs marked `preview_only`.
- Using a colleague’s payment terminal login.

## 8. Contacts

Payment ops desk: `payments@novaforge.example`  
After-hours pager tag: `#pay-oncall`
