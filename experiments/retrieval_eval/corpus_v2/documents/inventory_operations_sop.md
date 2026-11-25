# Inventory Operations SOP

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** OPS-INV-305  
**Effective Date:** January 20, 2026  
**Last Updated:** November 15, 2026  
**Owner:** Warehouse Systems

---

## 1. Purpose

Defines warehouse inventory states, cycle counts, quarantine, transfers, and allocation priority. Distinct from catalog reorder alerts in Product Documentation.

## 2. Inventory Buckets

| Bucket | Sellable? | May ship? |
|---|---|---|
| `AVAILABLE` | Yes | Yes |
| `RESERVED` | No | Yes (already allocated) |
| `QUARANTINE` | No | No |
| `DAMAGED` | No | No |
| `IN_TRANSIT` | No | No |
| `VENDOR_HOLD` | No | No |

Only `AVAILABLE` units may be newly allocated to orders.

## 3. Cycle Count Cadence

| ABC class | Count frequency | Variance escalate if | |
|---|---|---|
| A | Weekly | Absolute variance ≥ **8** units or **2%** of bin qty |
| B | Monthly | Absolute variance ≥ **15** units or **4%** |
| C | Quarterly | Absolute variance ≥ **25** units or **7%** |

Cycle counts freeze the bin for **20 minutes** or until count confirm, whichever shorter.

## 4. Quarantine Procedure

Warehouse associates must:

1. Move units to a `QUARANTINE` location within **25 minutes** of defect discovery.
2. Attach photo set (minimum **2** images) and defect code.
3. Notify Quality via ticket category `inv_quarantine`.
4. Quality disposition within **1 business day**: `return_to_available`, `rework`, `scrap`, or `vendor_rma`.
5. Scrap requires dual approval when extended cost exceeds **$750.00**.

## 5. Inter-Warehouse Transfers

- Transfer orders need a `transfer_id` and destination site code.
- Transit SLA between primary sites (PHX ↔ DAL): **3 calendar days**.
- Transit SLA involving the overflow site (RNO): **5 calendar days**.
- Receiving must complete putaway within **8 business hours** of dock arrival.
- Lost-in-transit transfers open incident type `INV-TRANSIT-LOSS` after SLA + **1 calendar day**.

## 6. Allocation Priority

When demand exceeds `AVAILABLE` stock, allocate in this order:

1. Orders marked `sla_critical`
2. Net-30 enterprise accounts with contract flag `priority_fulfill`
3. Standard prepaid orders by oldest `authorized` timestamp
4. Internal consumption orders

No more than **18%** of a day’s allocations may be tagged `sla_critical` without Inventory Manager override.

## 7. Safety Stock Floors

| Category family | Minimum `AVAILABLE` floor (per site) |
|---|---|
| Networking core SKUs | 12 units |
| Hot-swap power accessories | 40 units |
| Packing consumables | 200 units |

Breach of a floor creates a `stock_floor_breach` event; Procurement is paged if breach lasts **6 business hours**.

## 8. System Cutover Freeze

During OMS inventory cutovers, new allocations pause for a declared freeze window not to exceed **90 minutes**. Emergency ship exceptions require Director of Operations approval.
