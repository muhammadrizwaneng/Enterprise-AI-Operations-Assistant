# Returns Warehouse SOP

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** OPS-RMA-811  
**Effective Date:** August 1, 2026  
**Last Updated:** November 4, 2026  
**Owner:** Reverse Logistics

---

## 1. Scope

Inbound RMA receiving, grading, restock routing, and scrap at NovaForge returns docks. Consumer eligibility and restocking fee percentages remain in Refund Policy; this SOP covers **warehouse handling** after an RMA is approved.

## 2. RMA Intake States

| State | Meaning |
|---|---|
| `rma_approved` | Label issued; awaiting arrival |
| `rma_received` | Dock scan complete |
| `rma_grading` | QC in progress |
| `rma_restock` | Fit for `AVAILABLE` |
| `rma_refurb` | Sent to refurb lane |
| `rma_scrap` | Destroy / recycle |
| `rma_closed` | Financial and inventory complete |

Dock scan must occur within **2 business hours** of carrier delivery to the returns dock.

## 3. Grading Codes

| Grade | Definition | Inventory destination |
|---|---|---|
| `A` | Unopened / pristine | `AVAILABLE` |
| `B` | Opened, complete, cosmetic wear | `AVAILABLE` as `open_box` SKU suffix |
| `C` | Missing accessories | `REFURB` hold |
| `D` | Defective functional | `QUARANTINE` then vendor or scrap |
| `F` | Unsafe / liquid damage | `SCRAP` only |

Grading SLA: **1 business day** after `rma_received` for parcels under **40 lb**; **2 business days** for heavier parcels.

## 4. Receiving Procedure

Associates must:

1. Match RMA ID on label to OMS record.
2. Photograph exterior packaging (minimum **1** image) before opening.
3. Weigh parcel; variance beyond **12%** of expected weight flags `weight_mismatch`.
4. Apply grade code and bin location.
5. Trigger inventory adjustment within **25 minutes** of grade confirm.

Mismatch of serial vs RMA line blocks restock and opens ticket category `rma_serial_mismatch`.

## 5. Refurb and Scrap

- Refurb lane turnaround target: **5 business days**.
- Scrap certificates required for grades `F` and for `D` items with extended cost ≥ **$400.00**.
- Lithium battery returns require isolation cage placement within **15 minutes** of identification.

## 6. Customer Keep Decisions

When return shipping exceeds **$55.00** and merchandise value is under **$80.00**, agents may issue **keep-the-item** credit without inbound RMA, with Returns Lead approval.

## 7. Cross-Dock to Vendor

Vendor RMAs ship within **3 business days** of `D` disposition when a vendor RMA number exists. Missing vendor RMA numbers escalate after **1 business day**.

## 8. Contacts

Returns dock: `returns-dock@novaforge.example`  
Reverse logistics lead: `#rma-lead`
