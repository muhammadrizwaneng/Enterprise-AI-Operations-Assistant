# Access Control SOP

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** SEC-ACS-903  
**Effective Date:** September 9, 2026  
**Last Updated:** November 2, 2026  
**Owner:** IT Security Operations

---

## 1. Purpose

Controls joiner-mover-leaver access, privileged elevation, and vendor access to NovaForge systems. Distinct from handbook data-leak reporting timers and OS patch windows already evaluated historically.

## 2. Role Bundles

| Bundle | Includes | Recertify every |
|---|---|---|
| `RB-SUPPORT` | Ticket console, OMS read | 180 calendar days |
| `RB-OPS` | OMS write, WMS | 90 calendar days |
| `RB-FINANCE` | ERP AR/AP read-write | 90 calendar days |
| `RB-ADMIN` | IdP admin, secrets vault | 60 calendar days |
| `RB-VENDOR` | Scoped VPN + ticket plugin | 45 calendar days |

## 3. Joiner Procedure

1. HR ticket `access_joiner` with start date and manager.
2. Provision base bundle on start date − **1 business day**.
3. MFA enrollment deadline: end of first calendar day.
4. Failure to enroll MFA disables account at **18:00 local** on day 2.

## 4. Mover Procedure

- Role changes require manager approval in IdP workflow.
- Previous bundle removed within **8 business hours** of mover completion.
- Temporary dual-bundle periods must not exceed **5 business days**.

## 5. Leaver Procedure

1. Disable IdP login within **60 minutes** of HR leaver notice during business hours (**2 hours** after-hours).
2. Revoke tokens and API keys within **3 hours**.
3. Transfer owned tickets/queues within **1 business day**.
4. Privileged vault check-in confirmation required before closing leaver ticket.

## 6. Privileged Elevation (JIT)

| Elevation class | Max duration | Approver |
|---|---|---|
| `jit_prod_read` | 4 hours | Team lead |
| `jit_prod_write` | 2 hours | Service owner |
| `jit_breakglass` | 60 minutes | Security On-call + Director |

Break-glass events page `#sec-oncall` and open mandatory post-incident note within **24 hours**.

## 7. Vendor Access

- Vendors use `RB-VENDOR` only.
- Access windows must list start/end; default window length **21 calendar days**, renewable once without Security Manager review.
- Vendor sessions idle-timeout: **20 minutes**.
- File downloads to vendor devices require DLP tag `vendor_export` and ticket reference.

## 8. Audit Sampling

Security samples **5%** of JIT elevations weekly. Anomalies (duration overrun, missing approver) open finding tickets due in **3 business days**.

## 9. Contacts

Security ops: `access@novaforge.example`  
Break-glass: `#sec-oncall`
