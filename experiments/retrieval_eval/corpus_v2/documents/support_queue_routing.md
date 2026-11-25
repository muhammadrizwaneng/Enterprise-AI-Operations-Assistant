# Support Queue Routing Policy

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** CX-QUE-618  
**Effective Date:** June 8, 2026  
**Last Updated:** November 8, 2026  
**Owner:** Support Operations

---

## 1. Scope

Defines channel intake, queue assignment, reopen rules, and CSAT follow-up. Priority first-response targets in Customer Support Guidelines remain authoritative for priority tiers; this policy adds **channel** and **queue** rules not covered there.

## 2. Intake Channels

| Channel | Queue name | Staffed hours (local hub) | Auto-ack |
|---|---|---|---|
| Email | `q_email_general` | 07:00–21:00 | Immediate |
| Chat | `q_chat_live` | 08:00–20:00 | Immediate |
| Phone | `q_phone_tier1` | 08:00–18:00 | IVR only |
| Partner portal | `q_partner` | 09:00–17:00 | Immediate |
| Social mention | `q_social` | 10:00–19:00 | 15 minutes |

Phone abandon threshold before callback offer: **90 seconds**.

## 3. Skill-Based Routing

Tickets route by category to skill groups:

| Category token | Primary skill group | Backup |
|---|---|---|
| `billing_invoice` | Billing Specialists | Tier-2 Finance |
| `ship_exception` | Logistics Desk | Tier-1 General |
| `entitlement` | License Desk | Tier-2 Product |
| `identity` | Identity Ops | Tier-1 General |
| `partner_ops` | Partner Desk | Tier-2 Support |

If primary skill group occupancy exceeds **85%**, overflow to backup after **6 minutes** in queue.

## 4. Reopen Rules

1. Customers may reopen a `resolved` ticket within **10 calendar days** without a new ticket ID.
2. Reopens after **10 calendar days** create a linked child ticket.
3. Agents must not reopen `closed` tickets; they create a new ticket with `previous_ticket_id`.
4. Maximum reopens on the same ticket ID: **2**.

## 5. Follow-the-Sun Handoff

- Handoff packet required fields: summary, next action, customer timezone, commitment timestamp.
- Handoff incomplete checklist blocks queue transfer.
- Receiving hub must acknowledge within **35 minutes** during its staffed hours.

## 6. CSAT Sampling

| Channel | Sample rate | Survey send delay |
|---|---|---|
| Email | 40% of closed tickets | 2 hours after close |
| Chat | 60% | Immediate on close |
| Phone | 25% | 1 hour after close |
| Partner | 100% | 4 hours after close |

CSAT scores below **3.0** (5-point scale) auto-create a quality review task due in **2 business days**.

## 7. Emergency Broadcast Queue

Incident type `platform_outage` opens broadcast queue `q_broadcast`. All new non-identity tickets pause routing for up to **120 minutes** unless tagged `life_safety`.

## 8. Contacts

Queue ops: `queues@novaforge.example`  
Workforce desk: `#wfm-support`
