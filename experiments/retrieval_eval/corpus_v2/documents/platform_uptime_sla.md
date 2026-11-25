# Platform Uptime and Incident SLA

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** SRE-SLA-1107  
**Effective Date:** March 22, 2026  
**Last Updated:** November 1, 2026  
**Owner:** Site Reliability Engineering

---

## 1. Scope

Defines availability targets, severity definitions, customer communications, and maintenance windows for the NovaForge commerce and support platforms. Contractual credit math for invoice customers is executed via Finance Credit Memo type `CM-SLA`; this document supplies the operational triggers.

## 2. Availability Targets

| Service | Monthly uptime target | Measurement source |
|---|---|---|
| Storefront checkout | 99.90% | External synthetic checks |
| OMS API | 99.95% | Internal blackbox |
| Ticket console | 99.80% | Internal blackbox |
| Partner portal | 99.50% | External synthetic checks |
| Identity / login | 99.95% | External synthetic checks |

## 3. Severity Definitions

| Severity | Impact | Acknowledge | Mitigate |
|---|---|---|---|
| SEV-1 | Checkout or login down for all regions | 10 minutes | 60 minutes |
| SEV-2 | Single region or single payment method down | 20 minutes | 2 hours |
| SEV-3 | Degraded latency over 3× baseline | 45 minutes | 8 hours |
| SEV-4 | Cosmetic / non-buying path | 4 business hours | 3 business days |

## 4. Customer Communication Cadence

For SEV-1 and SEV-2:

1. Status page update within **15 minutes** of acknowledge.
2. Follow-up every **25 minutes** until mitigated.
3. Resolution summary within **2 business hours** after mitigate.
4. Postmortem published within **5 business days** for SEV-1 only.

Status page URL: `https://status.novaforge.example`.

## 5. Maintenance Windows

| Window code | UTC schedule | Max duration | Customer notice |
|---|---|---|---|
| `MW-WEEKLY` | Tue 06:00–08:00 | 90 minutes | 72 hours |
| `MW-MONTHLY` | First Sun 04:00–07:00 | 150 minutes | 5 calendar days |
| `MW-EMERGENCY` | As needed | 60 minutes | Best effort |

Overlapping `MW-WEEKLY` and `MW-MONTHLY` in the same week is prohibited.

## 6. Error Budget Policy

- When a service consumes **≥ 75%** of its monthly error budget, feature freezes apply to that service’s deploy pipeline.
- Error budget burn rate **≥ 2×** for 1 hour pages `#sre-primary`.
- Budget resets on the first calendar day of each month at **00:00 UTC**.

## 7. On-Call

Primary on-call rotation length: **8 calendar days**.  
Handoff checklist due **2 hours** before rotation end.  
Page ack timeout before secondary page: **8 minutes**.

## 8. Contacts

SRE desk: `sre@novaforge.example`  
Status edits: `#status-editors`
