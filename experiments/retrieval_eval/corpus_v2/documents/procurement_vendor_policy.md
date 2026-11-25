# Procurement and Vendor Policy

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** PRC-VEN-1004  
**Effective Date:** October 3, 2026  
**Last Updated:** October 30, 2026  
**Owner:** Procurement

---

## 1. Scope

Vendor onboarding, purchase orders (POs), inbound ASN rules, and scorecards. Does not redefine warehouse safety stock floors (Inventory Operations SOP) or catalog reorder alert quantities (Product Documentation).

## 2. Vendor Tiers

| Tier | Annual spend band | Required artifacts |
|---|---|---|
| `V1` | Under 50,000 | W-9/tax form, banking letter |
| `V2` | 50,000 – 250,000 | Above + insurance COI |
| `V3` | 250,000 – 1,000,000 | Above + SOC2 summary or equivalent |
| `V4` | Above 1,000,000 | Above + on-site audit every **36 months** |

New vendors default to `V1` until first PO posts.

## 3. Purchase Order Rules

1. POs are mandatory for goods receipts above **$200.00**.
2. Blind receipts without PO are blocked at dock systems.
3. PO line over-receipt tolerance: **5%** quantity or **$75.00** extended, whichever stricter.
4. Price variance beyond **3%** vs PO requires buyer acknowledgment before putaway.
5. Emergency POs after hours use prefix `EPO-` and need Director of Procurement ratification next business day.

## 4. ASN and Delivery Windows

| Inbound mode | ASN due before arrival | Delivery window adherence |
|---|---|---|
| Parcel | 4 hours | ± 1 business day |
| LTL | 1 business day | ± 4 hours of appointment |
| FTL | 2 business days | ± 2 hours of appointment |

Missed appointments without 6-hour notice incur dock reschedule fee code `DOCK-NOSHOW` (internal chargeback to buyer cost center).

## 5. Vendor Scorecard Metrics

| Metric | Target | Review cadence |
|---|---|---|
| On-time inbound | ≥ 92% | Monthly |
| Defect rate | ≤ 1.5% | Monthly |
| ASN accuracy | ≥ 95% | Monthly |
| Invoice match first-pass | ≥ 90% | Quarterly |

Vendors below target on **2** metrics for **2** consecutive months enter Performance Improvement Plan (PIP) lasting **60 calendar days**.

## 6. Corrective Action Procedure

Procurement buyers must:

1. Issue PIP letter with metric gaps.
2. Schedule checkpoint at day **30**.
3. At day **60**, decide `reinstate`, `volume_cap`, or `offboard`.
4. Offboard freezes new POs within **24 hours** of decision.
5. Open POs may complete; replacements need alternate vendor ID.

## 7. Ethical Sourcing Flags

Shipments from regions on the internal restricted list require Compliance pre-clear ticket `vendor_trade_review` with SLA **2 business days**.

## 8. Contacts

Procurement desk: `procurement@novaforge.example`  
Vendor onboarding: `#vendor-onboard`
