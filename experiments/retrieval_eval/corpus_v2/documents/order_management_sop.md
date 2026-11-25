# Order Management SOP

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** OPS-ORD-101  
**Effective Date:** March 1, 2026  
**Last Updated:** November 20, 2026  
**Owner:** Order Operations

---

## 1. Purpose

This SOP defines how NovaForge creates, edits, holds, splits, and cancels customer orders after checkout. It does not replace Delivery Policy or Refund Policy for carrier or repayment outcomes.

## 2. Order States

| State | Meaning | Editable line items? |
|---|---|---|
| `draft` | Cart converted but payment not authorized | Yes |
| `authorized` | Payment authorized; warehouse not yet allocated | Yes |
| `allocated` | Inventory reserved in a warehouse | Limited |
| `picking` | Pick wave started | No |
| `packed` | Carton closed; label may still be pending | No |
| `labeled` | Carrier label created | No |
| `shipped` | Carrier scan accepted | No |
| `fulfilled` | All lines delivered or closed | No |
| `cancelled` | Order voided before shipment | No |

Orders may not move from `shipped` directly to `cancelled`. Post-shipment returns use the Returns Warehouse SOP.

## 3. Edit Windows

1. Quantity and SKU swaps are allowed only while the order is in `draft` or `authorized`.
2. Ship-to address edits are allowed until the order reaches `labeled`.
3. After `allocated`, removing a line requires a **deallocation ticket** with reason code `CUST_CHANGE` or `STOCK_ERROR`.
4. Adding a new SKU after `allocated` creates a **child order** linked by `parent_order_id`; it does not reopen the parent pick wave.

## 4. Hold Codes

| Hold code | Who may place | Auto-release? |
|---|---|---|
| `FRAUD_REVIEW` | Risk team | No — manual clear |
| `PAYMENT_RETRY` | Billing bot | Yes after successful capture |
| `ADDRESS_VERIFY` | Support agent | Yes when address validation passes |
| `EXPORT_LICENSE` | Compliance | No — manual clear |
| `CUSTOMER_REQUEST` | Support agent | Yes after customer confirmation note |

Maximum concurrent holds on one order: **3**. A fourth hold attempt must escalate to the Order Operations Lead.

## 5. Split Shipment Rules

- Split shipments are allowed when at least one line is `allocated` and another remains `backordered`.
- The first split carton must ship within **2 business days** of the first allocation timestamp.
- Customers receive a split notification email from `orders@novaforge.example` when the second carton is labeled.
- Partial cancels on split orders apply only to unshipped lines.

## 6. Cancellation Procedure

Support agents must:

1. Confirm the current order state in the OMS.
2. If state is `draft`, `authorized`, or `allocated`, select **Cancel unshipped**.
3. If state is `picking` or `packed`, request warehouse stop-pick via channel `#wh-stops` and wait for ack code `STOP-OK`.
4. If state is `labeled` or later, do **not** cancel; open a return or carrier intercept per Carrier Exception Playbook.
5. Record cancellation reason code and agent ID on the order timeline.

## 7. Service Commitments

| Commitment | Target |
|---|---|
| Time to move `authorized` → `allocated` for in-region stock | 4 business hours |
| Customer notification of hold placement | 1 business hour |
| Child-order creation after approved add-on | 6 business hours |

## 8. Cross-References

- Payment capture failures: Payment Processing Policy.  
- Inventory reservation conflicts: Inventory Operations SOP.  
- Post-ship returns: Returns Warehouse SOP.
