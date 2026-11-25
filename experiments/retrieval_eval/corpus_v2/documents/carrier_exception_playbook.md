# Carrier Exception Playbook

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** OPS-CAR-704  
**Effective Date:** July 14, 2026  
**Last Updated:** November 6, 2026  
**Owner:** Logistics Desk

---

## 1. Purpose

Operational responses to carrier exceptions after a label exists. Complements Delivery Policy without restating free-shipping thresholds, adult-signature dollar triggers, or the 48-hour visible-damage customer report window.

## 2. Exception Codes

| Code | Meaning | First action SLA |
|---|---|---|
| `EX-NSR` | No scan received after ship | 16 business hours |
| `EX-DEX` | Delivery exception (access/weather) | 8 business hours |
| `EX-RTS` | Return to sender initiated by carrier | 4 business hours |
| `EX-MIS` | Mis-sort / wrong hub | 12 business hours |
| `EX-INT` | Customs hold | 1 business day |
| `EX-LOSS` | Carrier declared loss | 2 business hours |

## 3. Intercept Procedure

Logistics Desk must:

1. Confirm tracking shows pre-delivery status.
2. Submit carrier intercept request with account `#NF-CARRIER-MAIN`.
3. Record intercept confirmation number within the order timeline.
4. If intercept is denied, offer customer options: refuse delivery or accept and return.
5. Close `EX-*` ticket only after a terminal scan or replacement ship ID exists.

Intercept fee absorption: NovaForge pays intercept fees under **$35.00**; higher fees need Logistics Manager approval.

## 4. No-Scan Escalation Ladder

1. Hour 16: ping carrier API + email carrier desk.  
2. Hour 28: open carrier claim draft (do not file).  
3. Hour 40: file claim if still no scan.  
4. Hour 56: authorize replacement shipment for `sla_critical` orders.

## 5. Weather and Access Delays

- `EX-DEX` weather holds auto-extend customer promise dates by **1 business day** per carrier weather bulletin day, capped at **4** extensions.
- Access issues require a customer contact attempt every **business day** until resolved or reclassified to `EX-RTS`.

## 6. International Exceptions

| Region lane | Customs document re-send SLA | Broker contact attempts |
|---|---|---|
| CA/MX | 6 business hours | 2 |
| EU | 1 business day | 3 |
| APAC | 2 business days | 3 |

Duties unpaid by consignee after **5 business days** convert the shipment to `EX-RTS` unless the order is prepaid-DDP.

## 7. Replacement Authorization Matrix

| Order merchandise value | Approver for carrier-loss replacement |
|---|---|
| ≤ 600.00 | Logistics Specialist |
| 600.01 – 3,500.00 | Logistics Manager |
| Above 3,500.00 | Director of Operations |

## 8. Contacts

Logistics desk: `carriers@novaforge.example`  
On-call tag: `#carrier-ex`
