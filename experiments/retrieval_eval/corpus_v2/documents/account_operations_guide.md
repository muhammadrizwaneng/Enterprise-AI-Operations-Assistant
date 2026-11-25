# Account Operations Guide

**Company:** NovaForge Enterprise Solutions (fictional evaluation corpus)  
**Document ID:** CX-ACC-412  
**Effective Date:** April 5, 2026  
**Last Updated:** November 12, 2026  
**Owner:** Customer Identity Ops

---

## 1. Scope

Procedures for account creation, credential recovery, MFA, profile edits, merges, and closures. Privacy rights requests still route per Privacy Policy; this guide covers operational identity tooling.

## 2. Account Tiers

| Tier | Criteria | Concurrent sessions | API keys allowed |
|---|---|---|---|
| `starter` | Self-serve signup | 2 | 0 |
| `business` | Verified company domain | 5 | 2 |
| `enterprise` | Signed MSA | 25 | 10 |
| `partner` | Vendor/partner portal | 8 | 4 |

Upgrades from `starter` to `business` require domain verification within **48 business hours** of request.

## 3. Password Reset Procedure

Agents must:

1. Verify caller with **two** identity factors from the approved list (order number + billing ZIP, or registered phone OTP + security phrase).
2. Issue a single-use reset link expiring in **25 minutes**.
3. Invalidate all sessions except the reset session within **5 minutes** of password change.
4. Log reset reason code; do not read or set the customer’s new password.

Self-serve resets are limited to **5** successful resets per rolling **30 days**.

## 4. MFA Rules

- `enterprise` and `partner` tiers require MFA enrollment before the **second** login.
- Supported factors: authenticator app, hardware key, SMS (SMS allowed only as backup).
- MFA recovery codes: **8** single-use codes generated at enrollment.
- Lost-factor recovery requires a recorded video call for enterprise accounts or a notarized request for partner accounts.

## 5. Profile and Billing Address Changes

| Change type | Cool-down | Secondary approval |
|---|---|---|
| Display name | None | No |
| Login email | 24 hours | Email confirm on old and new |
| Billing address | 12 hours | Match last payment method country |
| Shipping address book entry | None | Fraud score under 70 |
| Tax ID | 72 hours | Finance Specialist |

Tax ID changes above cool-down still require ticket category `account_tax_change`.

## 6. Account Merge

1. Both accounts must share the same verified company domain **or** a matching tax ID.
2. Surviving account retains order history; source account is locked after merge.
3. Merge jobs run in batch at **03:30 UTC**; rush merges need Identity Ops Lead approval.
4. Maximum open merge requests per company: **2**.

## 7. Closure and Reactivation

- Soft close: login disabled; data retained per Privacy Policy.
- Hard close request acknowledgment SLA: **3 business days**.
- Reactivation of soft-closed accounts within **90 calendar days** requires only password reset + MFA.
- After **90 calendar days**, reactivation needs a new domain verification for business tiers.

## 8. Contacts

Identity ops: `accounts@novaforge.example`  
Urgent lockouts: tag `#id-lockout` (response target **20 minutes** during regional business hours)
