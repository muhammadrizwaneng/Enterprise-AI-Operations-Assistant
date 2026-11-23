# Product Documentation

**Company:** NovaForge Enterprise Solutions  
**Document ID:** PRD-DOC-004  
**Effective Date:** February 1, 2025  
**Last Updated:** November 10, 2026  
**Owner:** Product Management

---

## 1. Catalog Overview

NovaForge sells enterprise-ready technology across eight categories:

1. Laptops
2. Monitors
3. Peripherals
4. Networking
5. Storage
6. Software Licenses
7. Office Furniture
8. Accessories

Each product has a unique SKU in the format `SKU-<CAT>-####`.

## 2. SKU and Pricing Rules

- SKUs are immutable after publication.
- Unit prices are stored with two decimal places.
- Promotional pricing must be applied as order-level discounts, not by silently changing catalog unit prices.
- Inactive products remain in historical order items but cannot be newly ordered through the storefront.

## 3. Stock Management

- `stock_quantity` reflects sellable warehouse units.
- When stock reaches **10 units**, Procurement receives an automatic reorder alert.
- Negative stock is not permitted in production systems.
- Backorders require Operations Manager approval for quantities above **50 units**.

## 4. Category Guidance

### Laptops
Business notebooks with 12-month standard warranty. Optional 3-year extended warranty available as an accessory SKU.

### Monitors
Includes docking-compatible displays. Panel pixel defects follow ISO 9241-307 Class II criteria for replacement eligibility.

### Peripherals
Keyboards, mice, webcams, and docking stations. Firmware updates are published on the support portal quarterly.

### Networking
Switches, access points, and routers. Enterprise models include limited lifetime hardware warranty for manufacturing defects.

### Storage
SSDs, NAS devices, and backup appliances. Capacity figures use decimal (SI) gigabyte notation unless otherwise labeled.

### Software Licenses
Seat-based and floating licenses. Activation keys are delivered digitally after payment status is `completed`.

### Office Furniture
Desks, chairs, and storage cabinets. Freight delivery appointments are mandatory for packages over **70 lb**.

### Accessories
Cables, adapters, mounts, and spare batteries. Compatibility matrices are maintained per laptop family.

## 5. Warranty Summary

| Category | Standard Warranty | Extension Available |
|---|---|---|
| Laptops | 12 months | Yes (24 or 36 months) |
| Monitors | 24 months | Yes |
| Networking | Limited lifetime / 36 months | Model dependent |
| Storage | 36 months | Selected SKUs |
| Furniture | 24 months structural | No |
| Software | Term of license | N/A |

## 6. Returns Tied to Product Type

Opened software media and activated licenses follow the Refund Policy digital-goods rules. Hardware returns require original packaging when available.

## 7. Support Diagnostics

Before approving a hardware replacement, agents should collect:

- SKU and serial number
- Order number
- Failure description and reproduction steps
- Photos or diagnostic logs when relevant
