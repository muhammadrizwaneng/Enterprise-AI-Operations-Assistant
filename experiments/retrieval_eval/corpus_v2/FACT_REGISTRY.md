# Corpus v2 Fact Registry

Traceable fact atoms for evaluation-only NovaForge documents under `corpus_v2/documents/`.
Fictional evaluation content — **not** real SeeBiz production policy.

**Total registered facts:** 217

## Schema

| Field | Meaning |
|---|---|
| Fact ID | Stable unique identifier |
| Source document | File in `documents/` |
| Section | Heading anchor in source |
| Supporting evidence | Exact substring present in source |
| Normalized fact | Independent testable claim |
| Topic | Coarse category |
| Independently testable | Yes/No |
| Related fact IDs | Optional links |

## Facts

| Fact ID | Source document | Section | Supporting evidence | Normalized fact | Topic | Testable | Related |
|---|---|---|---|---|---|---|---|
| F-ORD-001 | `order_management_sop.md` | ## 2. Order States | `draft` \| Cart converted but payment not authorized | Order state draft: payment not authorized | order_states | Yes | — |
| F-ORD-002 | `order_management_sop.md` | ## 2. Order States | `labeled` \| Carrier label created | Order state labeled: carrier label created | order_states | Yes | — |
| F-ORD-003 | `order_management_sop.md` | ## 2. Order States | Orders may not move from `shipped` directly to `cancelled` | Cannot move shipped→cancelled | order_transitions | Yes | — |
| F-ORD-004 | `order_management_sop.md` | ## 3. Edit Windows | Quantity and SKU swaps are allowed only while the order is in `draft` or `authorized` | SKU/qty edits only in draft or authorized | order_edits | Yes | — |
| F-ORD-005 | `order_management_sop.md` | ## 3. Edit Windows | Ship-to address edits are allowed until the order reaches `labeled` | Ship-to editable until labeled | order_edits | Yes | F-ORD-002 |
| F-ORD-006 | `order_management_sop.md` | ## 3. Edit Windows | reason code `CUST_CHANGE` or `STOCK_ERROR` | Deallocation codes CUST_CHANGE or STOCK_ERROR | order_edits | Yes | — |
| F-ORD-007 | `order_management_sop.md` | ## 3. Edit Windows | creates a **child order** linked by `parent_order_id` | Add-on after allocate creates child order | order_edits | Yes | — |
| F-ORD-008 | `order_management_sop.md` | ## 4. Hold Codes | `FRAUD_REVIEW` \| Risk team \| No — manual clear | FRAUD_REVIEW: Risk team, manual clear | order_holds | Yes | — |
| F-ORD-009 | `order_management_sop.md` | ## 4. Hold Codes | `PAYMENT_RETRY` \| Billing bot \| Yes after successful capture | PAYMENT_RETRY auto-releases after capture | order_holds | Yes | — |
| F-ORD-010 | `order_management_sop.md` | ## 4. Hold Codes | Maximum concurrent holds on one order: **3** | Max concurrent holds: 3 | order_holds | Yes | — |
| F-ORD-011 | `order_management_sop.md` | ## 4. Hold Codes | fourth hold attempt must escalate to the Order Operations Lead | Fourth hold → Order Operations Lead | order_holds | Yes | F-ORD-010 |
| F-ORD-012 | `order_management_sop.md` | ## 5. Split Shipment Rules | first split carton must ship within **2 business days** of the first allocation timestamp | First split carton within 2 business days of allocation | split_ship | Yes | — |
| F-ORD-013 | `order_management_sop.md` | ## 5. Split Shipment Rules | orders@novaforge.example | Split email from orders@novaforge.example | split_ship | Yes | — |
| F-ORD-014 | `order_management_sop.md` | ## 6. Cancellation Procedure | channel `#wh-stops` | Stop-pick via #wh-stops | cancel_proc | Yes | — |
| F-ORD-015 | `order_management_sop.md` | ## 6. Cancellation Procedure | ack code `STOP-OK` | Stop-pick ack STOP-OK | cancel_proc | Yes | F-ORD-014 |
| F-ORD-016 | `order_management_sop.md` | ## 6. Cancellation Procedure | If state is `labeled` or later, do **not** cancel | No cancel at labeled or later | cancel_proc | Yes | — |
| F-ORD-017 | `order_management_sop.md` | ## 7. Service Commitments | 4 business hours | Authorized→allocated target 4 business hours | order_sla | Yes | — |
| F-ORD-018 | `order_management_sop.md` | ## 7. Service Commitments | Customer notification of hold placement \| 1 business hour | Hold notify within 1 business hour | order_sla | Yes | — |
| F-ORD-019 | `order_management_sop.md` | ## 7. Service Commitments | Child-order creation after approved add-on \| 6 business hours | Child-order creation within 6 business hours | order_sla | Yes | F-ORD-007 |
| F-PAY-001 | `payment_processing_policy.md` | ## 2. Authorization and Capture | On `allocated` or 18 hours after auth, whichever first | Card online capture on allocated or 18h | pay_capture | Yes | — |
| F-PAY-002 | `payment_processing_policy.md` | ## 2. Authorization and Capture | 8 calendar days | Card online auth hold TTL 8 calendar days | pay_auth | Yes | — |
| F-PAY-003 | `payment_processing_policy.md` | ## 2. Authorization and Capture | 5 calendar days | Phone card auth TTL 5 calendar days | pay_auth | Yes | — |
| F-PAY-004 | `payment_processing_policy.md` | ## 2. Authorization and Capture | ACH debit \| Checkout submit \| After `packed` | ACH capture after packed | pay_capture | Yes | — |
| F-PAY-005 | `payment_processing_policy.md` | ## 2. Authorization and Capture | On `labeled` \| 10 calendar days | Wallet capture on labeled; TTL 10 calendar days | pay_capture | Yes | — |
| F-PAY-006 | `payment_processing_policy.md` | ## 2. Authorization and Capture | `CAP-EARLY` | Early capture code CAP-EARLY | pay_capture | Yes | — |
| F-PAY-007 | `payment_processing_policy.md` | ## 3. Failed Payment Handling | **T+2 hours** and **T+26 hours** | Soft decline retries T+2h and T+26h | pay_fail | Yes | — |
| F-PAY-008 | `payment_processing_policy.md` | ## 3. Failed Payment Handling | within **45 minutes** | Hard decline email within 45 minutes | pay_fail | Yes | — |
| F-PAY-009 | `payment_processing_policy.md` | ## 3. Failed Payment Handling | After **3** failed capture attempts | Cancel unshipped after 3 failed captures | pay_fail | Yes | — |
| F-PAY-010 | `payment_processing_policy.md` | ## 3. Failed Payment Handling | once per clock hour | Max one manual capture retry per clock hour | pay_fail | Yes | — |
| F-PAY-011 | `payment_processing_policy.md` | ## 4. Settlement Batches | **22:00 UTC** daily | Card settlement 22:00 UTC daily | pay_settle | Yes | — |
| F-PAY-012 | `payment_processing_policy.md` | ## 4. Settlement Batches | **14:00 UTC** | ACH settlement 14:00 UTC banking days | pay_settle | Yes | — |
| F-PAY-013 | `payment_processing_policy.md` | ## 4. Settlement Batches | **36 hours** | Unmatched settlement >36h → settle_mismatch | pay_settle | Yes | — |
| F-PAY-014 | `payment_processing_policy.md` | ## 5. Chargebacks | Inquiry received \| Billing Specialist \| 2 business days | Chargeback inquiry SLA 2 business days | pay_cb | Yes | — |
| F-PAY-015 | `payment_processing_policy.md` | ## 5. Chargebacks | Hard chargeback \| Billing Supervisor \| 7 business days | Hard chargeback SLA 7 business days | pay_cb | Yes | — |
| F-PAY-016 | `payment_processing_policy.md` | ## 5. Chargebacks | **3** attachments | Evidence pack min 3 attachments | pay_cb | Yes | — |
| F-PAY-017 | `payment_processing_policy.md` | ## 5. Chargebacks | **$4,000.00** | Chargebacks >$4000 need Treasury Lead ack in 4bh | pay_cb | Yes | — |
| F-PAY-018 | `payment_processing_policy.md` | ## 6. Credits vs Refunds | within **1 business day** of approval | Store credit posts within 1 business day | pay_credit | Yes | — |
| F-PAY-019 | `payment_processing_policy.md` | ## 6. Credits vs Refunds | within **2 business hours** of refund approval | Capture reversal within 2bh of refund approval | pay_credit | Yes | — |
| F-PAY-020 | `payment_processing_policy.md` | ## 6. Credits vs Refunds | **$1.00** residual | Partial reversal residual floor $1.00 | pay_credit | Yes | — |
| F-PAY-021 | `payment_processing_policy.md` | ## 7. Prohibited Actions | more than **4** separate captures | Max 4 captures per order | pay_prohibit | Yes | — |
| F-PAY-022 | `payment_processing_policy.md` | ## 7. Prohibited Actions | `preview_only` | No capture for preview_only SKUs | pay_prohibit | Yes | — |
| F-PAY-023 | `payment_processing_policy.md` | ## 8. Contacts | payments@novaforge.example | payments@novaforge.example | pay_contact | Yes | — |
| F-INV-001 | `inventory_operations_sop.md` | ## 2. Inventory Buckets | `AVAILABLE` \| Yes \| Yes | AVAILABLE sellable and shippable | inv_buckets | Yes | — |
| F-INV-002 | `inventory_operations_sop.md` | ## 2. Inventory Buckets | `QUARANTINE` \| No \| No | QUARANTINE not sellable | inv_buckets | Yes | — |
| F-INV-003 | `inventory_operations_sop.md` | ## 2. Inventory Buckets | Only `AVAILABLE` units may be newly allocated | Only AVAILABLE newly allocated | inv_buckets | Yes | — |
| F-INV-004 | `inventory_operations_sop.md` | ## 3. Cycle Count Cadence | A \| Weekly \| Absolute variance ≥ **8** units or **2%** | Class A weekly; escalate ≥8 or 2% | inv_count | Yes | — |
| F-INV-005 | `inventory_operations_sop.md` | ## 3. Cycle Count Cadence | B \| Monthly \| Absolute variance ≥ **15** units or **4%** | Class B monthly; escalate ≥15 or 4% | inv_count | Yes | — |
| F-INV-006 | `inventory_operations_sop.md` | ## 3. Cycle Count Cadence | C \| Quarterly \| Absolute variance ≥ **25** units or **7%** | Class C quarterly; escalate ≥25 or 7% | inv_count | Yes | — |
| F-INV-007 | `inventory_operations_sop.md` | ## 3. Cycle Count Cadence | **20 minutes** | Cycle count freezes bin 20 minutes | inv_count | Yes | — |
| F-INV-008 | `inventory_operations_sop.md` | ## 4. Quarantine Procedure | within **25 minutes** of defect discovery | Quarantine move within 25 minutes | inv_quar | Yes | — |
| F-INV-009 | `inventory_operations_sop.md` | ## 4. Quarantine Procedure | minimum **2** images | Quarantine photos min 2 | inv_quar | Yes | — |
| F-INV-010 | `inventory_operations_sop.md` | ## 4. Quarantine Procedure | `inv_quarantine` | Ticket category inv_quarantine | inv_quar | Yes | — |
| F-INV-011 | `inventory_operations_sop.md` | ## 4. Quarantine Procedure | within **1 business day** | Quality disposition within 1 business day | inv_quar | Yes | — |
| F-INV-012 | `inventory_operations_sop.md` | ## 4. Quarantine Procedure | **$750.00** | Scrap dual approval if cost >$750 | inv_quar | Yes | — |
| F-INV-013 | `inventory_operations_sop.md` | ## 5. Inter-Warehouse Transfers | **3 calendar days** | PHX↔DAL transit SLA 3 calendar days | inv_xfer | Yes | — |
| F-INV-014 | `inventory_operations_sop.md` | ## 5. Inter-Warehouse Transfers | **5 calendar days** | RNO transit SLA 5 calendar days | inv_xfer | Yes | — |
| F-INV-015 | `inventory_operations_sop.md` | ## 5. Inter-Warehouse Transfers | **8 business hours** | Putaway within 8 business hours | inv_xfer | Yes | — |
| F-INV-016 | `inventory_operations_sop.md` | ## 5. Inter-Warehouse Transfers | `INV-TRANSIT-LOSS` | Transit loss type INV-TRANSIT-LOSS after SLA+1 day | inv_xfer | Yes | — |
| F-INV-017 | `inventory_operations_sop.md` | ## 6. Allocation Priority | `sla_critical` | Priority 1: sla_critical orders | inv_alloc | Yes | — |
| F-INV-018 | `inventory_operations_sop.md` | ## 6. Allocation Priority | `priority_fulfill` | Priority 2: priority_fulfill accounts | inv_alloc | Yes | — |
| F-INV-019 | `inventory_operations_sop.md` | ## 6. Allocation Priority | **18%** | Max 18% daily allocations sla_critical | inv_alloc | Yes | — |
| F-INV-020 | `inventory_operations_sop.md` | ## 7. Safety Stock Floors | Networking core SKUs \| 12 units | Networking floor 12/site | inv_floor | Yes | — |
| F-INV-021 | `inventory_operations_sop.md` | ## 7. Safety Stock Floors | Hot-swap power accessories \| 40 units | Power accessories floor 40/site | inv_floor | Yes | — |
| F-INV-022 | `inventory_operations_sop.md` | ## 7. Safety Stock Floors | Packing consumables \| 200 units | Packing consumables floor 200/site | inv_floor | Yes | — |
| F-INV-023 | `inventory_operations_sop.md` | ## 7. Safety Stock Floors | **6 business hours** | Page Procurement if floor breach lasts 6bh | inv_floor | Yes | — |
| F-INV-024 | `inventory_operations_sop.md` | ## 8. System Cutover Freeze | **90 minutes** | Cutover freeze max 90 minutes | inv_freeze | Yes | — |
| F-ACC-001 | `account_operations_guide.md` | ## 2. Account Tiers | `starter` \| Self-serve signup \| 2 \| 0 | Starter: 2 sessions, 0 API keys | acct_tier | Yes | — |
| F-ACC-002 | `account_operations_guide.md` | ## 2. Account Tiers | `enterprise` \| Signed MSA \| 25 \| 10 | Enterprise: 25 sessions, 10 API keys | acct_tier | Yes | — |
| F-ACC-003 | `account_operations_guide.md` | ## 2. Account Tiers | **48 business hours** | Domain verify within 48 business hours | acct_tier | Yes | — |
| F-ACC-004 | `account_operations_guide.md` | ## 3. Password Reset Procedure | **two** identity factors | Reset requires two identity factors | acct_reset | Yes | — |
| F-ACC-005 | `account_operations_guide.md` | ## 3. Password Reset Procedure | **25 minutes** | Reset link expires in 25 minutes | acct_reset | Yes | — |
| F-ACC-006 | `account_operations_guide.md` | ## 3. Password Reset Procedure | within **5 minutes** of password change | Invalidate other sessions within 5 minutes | acct_reset | Yes | — |
| F-ACC-007 | `account_operations_guide.md` | ## 3. Password Reset Procedure | **5** successful resets per rolling **30 days** | Self-serve reset limit 5/30 days | acct_reset | Yes | — |
| F-ACC-008 | `account_operations_guide.md` | ## 4. MFA Rules | before the **second** login | Enterprise/partner MFA before second login | acct_mfa | Yes | — |
| F-ACC-009 | `account_operations_guide.md` | ## 4. MFA Rules | **8** single-use codes | MFA recovery codes: 8 | acct_mfa | Yes | — |
| F-ACC-010 | `account_operations_guide.md` | ## 4. MFA Rules | notarized request for partner accounts | Partner lost-factor may use notarized request | acct_mfa | Yes | — |
| F-ACC-011 | `account_operations_guide.md` | ## 5. Profile and Billing Address Changes | Login email \| 24 hours | Login email cool-down 24 hours | acct_profile | Yes | — |
| F-ACC-012 | `account_operations_guide.md` | ## 5. Profile and Billing Address Changes | Billing address \| 12 hours | Billing address cool-down 12 hours | acct_profile | Yes | — |
| F-ACC-013 | `account_operations_guide.md` | ## 5. Profile and Billing Address Changes | Tax ID \| 72 hours | Tax ID cool-down 72 hours | acct_profile | Yes | — |
| F-ACC-014 | `account_operations_guide.md` | ## 5. Profile and Billing Address Changes | Fraud score under 70 | Shipping address book if fraud score under 70 | acct_profile | Yes | — |
| F-ACC-015 | `account_operations_guide.md` | ## 5. Profile and Billing Address Changes | `account_tax_change` | Tax ID ticket account_tax_change | acct_profile | Yes | — |
| F-ACC-016 | `account_operations_guide.md` | ## 6. Account Merge | **2** | Max 2 open merges per company | acct_merge | Yes | — |
| F-ACC-017 | `account_operations_guide.md` | ## 6. Account Merge | **03:30 UTC** | Merge batch 03:30 UTC | acct_merge | Yes | — |
| F-ACC-018 | `account_operations_guide.md` | ## 7. Closure and Reactivation | **3 business days** | Hard close ack SLA 3 business days | acct_close | Yes | — |
| F-ACC-019 | `account_operations_guide.md` | ## 7. Closure and Reactivation | **90 calendar days** | Soft-close reactivation within 90 calendar days | acct_close | Yes | — |
| F-ACC-020 | `account_operations_guide.md` | ## 8. Contacts | accounts@novaforge.example | accounts@novaforge.example | acct_contact | Yes | — |
| F-ACC-021 | `account_operations_guide.md` | ## 8. Contacts | **20 minutes** | #id-lockout target 20 minutes | acct_contact | Yes | — |
| F-FIN-001 | `finance_credit_memo_policy.md` | ## 2. Credit Memo Types | `CM-PRICE` | CM-PRICE for pricing errors | fin_cm_type | Yes | — |
| F-FIN-002 | `finance_credit_memo_policy.md` | ## 2. Credit Memo Types | `CM-SLA` | CM-SLA for SLA credits | fin_cm_type | Yes | — |
| F-FIN-003 | `finance_credit_memo_policy.md` | ## 3. Approval Matrix | ≤ 250.00 \| Billing Specialist | CM ≤$250: Billing Specialist | fin_cm_appr | Yes | — |
| F-FIN-004 | `finance_credit_memo_policy.md` | ## 3. Approval Matrix | 250.01 – 1,500.00 \| Billing Supervisor | CM $250.01–1500: Billing Supervisor | fin_cm_appr | Yes | — |
| F-FIN-005 | `finance_credit_memo_policy.md` | ## 3. Approval Matrix | 1,500.01 – 8,000.00 \| Finance Manager | CM $1500.01–8000: Finance Manager | fin_cm_appr | Yes | — |
| F-FIN-006 | `finance_credit_memo_policy.md` | ## 3. Approval Matrix | 8,000.01 – 25,000.00 \| Controller | CM $8000.01–25000: Controller | fin_cm_appr | Yes | — |
| F-FIN-007 | `finance_credit_memo_policy.md` | ## 3. Approval Matrix | Above 25,000.00 \| CFO delegate | CM above $25000: CFO delegate | fin_cm_appr | Yes | — |
| F-FIN-008 | `finance_credit_memo_policy.md` | ## 3. Approval Matrix | Self-approval is prohibited | CM self-approval prohibited | fin_cm_appr | Yes | — |
| F-FIN-009 | `finance_credit_memo_policy.md` | ## 4. Issuance Procedure | `credit_memo` | Ticket category credit_memo | fin_cm_proc | Yes | — |
| F-FIN-010 | `finance_credit_memo_policy.md` | ## 4. Issuance Procedure | within **1 business day** of final approval | Post CM within 1 business day of approval | fin_cm_proc | Yes | — |
| F-FIN-011 | `finance_credit_memo_policy.md` | ## 4. Issuance Procedure | within **4 business hours** of posting | Email CM PDF within 4bh of posting | fin_cm_proc | Yes | — |
| F-FIN-012 | `finance_credit_memo_policy.md` | ## 5. Aging and Application | **60 calendar days** | Unapplied CM >60 days on exception report | fin_cm_age | Yes | — |
| F-FIN-013 | `finance_credit_memo_policy.md` | ## 5. Aging and Application | **180 calendar days** | CM >180 days needs Controller review | fin_cm_age | Yes | — |
| F-FIN-014 | `finance_credit_memo_policy.md` | ## 6. SLA Credits | ≥ **45** | CM-SLA needs ≥45 downtime minutes/month | fin_cm_sla | Yes | — |
| F-FIN-015 | `finance_credit_memo_policy.md` | ## 6. SLA Credits | ≥ **3** | CM-SLA alt ≥3 missed commitments | fin_cm_sla | Yes | F-FIN-014 |
| F-FIN-016 | `finance_credit_memo_policy.md` | ## 6. SLA Credits | **12%** | Max CM-SLA 12% quarterly recurring fees | fin_cm_sla | Yes | — |
| F-FIN-017 | `finance_credit_memo_policy.md` | ## 7. Documentation Retention | **5 years** | CM packets retained 5 years | fin_cm_ret | Yes | — |
| F-FIN-018 | `finance_credit_memo_policy.md` | ## 7. Documentation Retention | `fin-cm-archive` | Archive bucket fin-cm-archive | fin_cm_ret | Yes | — |
| F-FIN-019 | `finance_credit_memo_policy.md` | ## 8. Contacts | creditmemos@novaforge.example | creditmemos@novaforge.example | fin_cm_contact | Yes | — |
| F-QUE-001 | `support_queue_routing.md` | ## 2. Intake Channels | `q_chat_live` \| 08:00–20:00 | Chat queue q_chat_live 08:00–20:00 | que_channel | Yes | — |
| F-QUE-002 | `support_queue_routing.md` | ## 2. Intake Channels | `q_phone_tier1` \| 08:00–18:00 | Phone queue q_phone_tier1 08:00–18:00 | que_channel | Yes | — |
| F-QUE-003 | `support_queue_routing.md` | ## 2. Intake Channels | 15 minutes | Social auto-ack within 15 minutes | que_channel | Yes | — |
| F-QUE-004 | `support_queue_routing.md` | ## 2. Intake Channels | **90 seconds** | Phone abandon callback after 90 seconds | que_channel | Yes | — |
| F-QUE-005 | `support_queue_routing.md` | ## 3. Skill-Based Routing | `billing_invoice` \| Billing Specialists | billing_invoice → Billing Specialists | que_skill | Yes | — |
| F-QUE-006 | `support_queue_routing.md` | ## 3. Skill-Based Routing | `ship_exception` \| Logistics Desk | ship_exception → Logistics Desk | que_skill | Yes | — |
| F-QUE-007 | `support_queue_routing.md` | ## 3. Skill-Based Routing | **85%** | Overflow when occupancy >85% | que_skill | Yes | — |
| F-QUE-008 | `support_queue_routing.md` | ## 3. Skill-Based Routing | **6 minutes** | Overflow after 6 minutes in queue | que_skill | Yes | F-QUE-007 |
| F-QUE-009 | `support_queue_routing.md` | ## 4. Reopen Rules | **10 calendar days** | Reopen resolved within 10 calendar days | que_reopen | Yes | — |
| F-QUE-010 | `support_queue_routing.md` | ## 4. Reopen Rules | Maximum reopens on the same ticket ID: **2** | Max 2 reopens per ticket ID | que_reopen | Yes | — |
| F-QUE-011 | `support_queue_routing.md` | ## 4. Reopen Rules | must not reopen `closed` tickets | Cannot reopen closed tickets | que_reopen | Yes | — |
| F-QUE-012 | `support_queue_routing.md` | ## 5. Follow-the-Sun Handoff | **35 minutes** | Receiving hub ack within 35 minutes | que_handoff | Yes | — |
| F-QUE-013 | `support_queue_routing.md` | ## 6. CSAT Sampling | Email \| 40% | Email CSAT sample 40% | que_csat | Yes | — |
| F-QUE-014 | `support_queue_routing.md` | ## 6. CSAT Sampling | Partner \| 100% | Partner CSAT sample 100% | que_csat | Yes | — |
| F-QUE-015 | `support_queue_routing.md` | ## 6. CSAT Sampling | below **3.0** | CSAT below 3.0 → quality review in 2bd | que_csat | Yes | — |
| F-QUE-016 | `support_queue_routing.md` | ## 7. Emergency Broadcast Queue | **120 minutes** | Broadcast pause up to 120 minutes | que_broadcast | Yes | — |
| F-QUE-017 | `support_queue_routing.md` | ## 7. Emergency Broadcast Queue | `life_safety` | life_safety exempt from pause | que_broadcast | Yes | — |
| F-QUE-018 | `support_queue_routing.md` | ## 8. Contacts | queues@novaforge.example | queues@novaforge.example | que_contact | Yes | — |
| F-CAR-001 | `carrier_exception_playbook.md` | ## 2. Exception Codes | `EX-NSR` \| No scan received after ship \| 16 business hours | EX-NSR SLA 16 business hours | car_code | Yes | — |
| F-CAR-002 | `carrier_exception_playbook.md` | ## 2. Exception Codes | `EX-RTS` \| Return to sender initiated by carrier \| 4 business hours | EX-RTS SLA 4 business hours | car_code | Yes | — |
| F-CAR-003 | `carrier_exception_playbook.md` | ## 2. Exception Codes | `EX-LOSS` \| Carrier declared loss \| 2 business hours | EX-LOSS SLA 2 business hours | car_code | Yes | — |
| F-CAR-004 | `carrier_exception_playbook.md` | ## 3. Intercept Procedure | `#NF-CARRIER-MAIN` | Intercept account #NF-CARRIER-MAIN | car_intercept | Yes | — |
| F-CAR-005 | `carrier_exception_playbook.md` | ## 3. Intercept Procedure | **$35.00** | Pay intercept fees under $35 | car_intercept | Yes | — |
| F-CAR-006 | `carrier_exception_playbook.md` | ## 4. No-Scan Escalation Ladder | Hour 16: | NSR hour 16: ping carrier API | car_nsr | Yes | — |
| F-CAR-007 | `carrier_exception_playbook.md` | ## 4. No-Scan Escalation Ladder | Hour 40: | NSR hour 40: file claim | car_nsr | Yes | — |
| F-CAR-008 | `carrier_exception_playbook.md` | ## 4. No-Scan Escalation Ladder | Hour 56: | NSR hour 56: authorize replacement for sla_critical | car_nsr | Yes | — |
| F-CAR-009 | `carrier_exception_playbook.md` | ## 5. Weather and Access Delays | capped at **4** extensions | Weather extensions capped at 4 | car_weather | Yes | — |
| F-CAR-010 | `carrier_exception_playbook.md` | ## 5. Weather and Access Delays | **1 business day** per carrier weather bulletin day | +1 business day per weather bulletin day | car_weather | Yes | — |
| F-CAR-011 | `carrier_exception_playbook.md` | ## 6. International Exceptions | CA/MX \| 6 business hours | CA/MX customs re-send 6bh | car_intl | Yes | — |
| F-CAR-012 | `carrier_exception_playbook.md` | ## 6. International Exceptions | EU \| 1 business day \| 3 | EU customs re-send 1bd | car_intl | Yes | — |
| F-CAR-013 | `carrier_exception_playbook.md` | ## 6. International Exceptions | **5 business days** convert the shipment to `EX-RTS` | Unpaid duties after 5bd → EX-RTS unless DDP | car_intl | Yes | — |
| F-CAR-014 | `carrier_exception_playbook.md` | ## 7. Replacement Authorization Matrix | ≤ 600.00 \| Logistics Specialist | Replacement ≤$600: Logistics Specialist | car_repl | Yes | — |
| F-CAR-015 | `carrier_exception_playbook.md` | ## 7. Replacement Authorization Matrix | 600.01 – 3,500.00 \| Logistics Manager | $600.01–3500: Logistics Manager | car_repl | Yes | — |
| F-CAR-016 | `carrier_exception_playbook.md` | ## 7. Replacement Authorization Matrix | Above 3,500.00 \| Director of Operations | Above $3500: Director of Operations | car_repl | Yes | — |
| F-CAR-017 | `carrier_exception_playbook.md` | ## 8. Contacts | carriers@novaforge.example | carriers@novaforge.example | car_contact | Yes | — |
| F-RMA-001 | `returns_warehouse_sop.md` | ## 2. RMA Intake States | `rma_received` \| Dock scan complete | rma_received = dock scan complete | rma_state | Yes | — |
| F-RMA-002 | `returns_warehouse_sop.md` | ## 2. RMA Intake States | **2 business hours** | Dock scan within 2bh of delivery | rma_state | Yes | — |
| F-RMA-003 | `returns_warehouse_sop.md` | ## 3. Grading Codes | `A` \| Unopened / pristine \| `AVAILABLE` | Grade A → AVAILABLE | rma_grade | Yes | — |
| F-RMA-004 | `returns_warehouse_sop.md` | ## 3. Grading Codes | `open_box` | Grade B → AVAILABLE open_box | rma_grade | Yes | — |
| F-RMA-005 | `returns_warehouse_sop.md` | ## 3. Grading Codes | `F` \| Unsafe / liquid damage \| `SCRAP` only | Grade F → SCRAP only | rma_grade | Yes | — |
| F-RMA-006 | `returns_warehouse_sop.md` | ## 3. Grading Codes | under **40 lb** | Grading SLA 1bd under 40 lb | rma_grade | Yes | — |
| F-RMA-007 | `returns_warehouse_sop.md` | ## 4. Receiving Procedure | minimum **1** image | Photo exterior before opening | rma_recv | Yes | — |
| F-RMA-008 | `returns_warehouse_sop.md` | ## 4. Receiving Procedure | **12%** | Weight mismatch if variance >12% | rma_recv | Yes | — |
| F-RMA-009 | `returns_warehouse_sop.md` | ## 4. Receiving Procedure | within **25 minutes** of grade confirm | Inventory adjust within 25 minutes of grade | rma_recv | Yes | — |
| F-RMA-010 | `returns_warehouse_sop.md` | ## 4. Receiving Procedure | `rma_serial_mismatch` | Serial mismatch ticket rma_serial_mismatch | rma_recv | Yes | — |
| F-RMA-011 | `returns_warehouse_sop.md` | ## 5. Refurb and Scrap | **5 business days** | Refurb turnaround 5 business days | rma_refurb | Yes | — |
| F-RMA-012 | `returns_warehouse_sop.md` | ## 5. Refurb and Scrap | **$400.00** | Scrap certificate for D if cost ≥$400 | rma_refurb | Yes | — |
| F-RMA-013 | `returns_warehouse_sop.md` | ## 5. Refurb and Scrap | **15 minutes** | Lithium isolation within 15 minutes | rma_refurb | Yes | — |
| F-RMA-014 | `returns_warehouse_sop.md` | ## 6. Customer Keep Decisions | **$55.00** and merchandise value is under **$80.00** | Keep-item if ship>$55 and value<$80 | rma_keep | Yes | — |
| F-RMA-015 | `returns_warehouse_sop.md` | ## 7. Cross-Dock to Vendor | **3 business days** of `D` disposition | Vendor RMA ship within 3bd of D | rma_vendor | Yes | — |
| F-RMA-016 | `returns_warehouse_sop.md` | ## 7. Cross-Dock to Vendor | after **1 business day** | Missing vendor RMA# escalates after 1bd | rma_vendor | Yes | — |
| F-RMA-017 | `returns_warehouse_sop.md` | ## 8. Contacts | returns-dock@novaforge.example | returns-dock@novaforge.example | rma_contact | Yes | — |
| F-ACS-001 | `access_control_sop.md` | ## 2. Role Bundles | `RB-SUPPORT` \| Ticket console, OMS read \| 180 calendar days | RB-SUPPORT recertify 180 days | acs_bundle | Yes | — |
| F-ACS-002 | `access_control_sop.md` | ## 2. Role Bundles | `RB-ADMIN` \| IdP admin, secrets vault \| 60 calendar days | RB-ADMIN recertify 60 days | acs_bundle | Yes | — |
| F-ACS-003 | `access_control_sop.md` | ## 2. Role Bundles | `RB-VENDOR` \| Scoped VPN + ticket plugin \| 45 calendar days | RB-VENDOR recertify 45 days | acs_bundle | Yes | — |
| F-ACS-004 | `access_control_sop.md` | ## 3. Joiner Procedure | − **1 business day** | Provision start date −1 business day | acs_joiner | Yes | — |
| F-ACS-005 | `access_control_sop.md` | ## 3. Joiner Procedure | **18:00 local** on day 2 | No MFA → disable 18:00 local day 2 | acs_joiner | Yes | — |
| F-ACS-006 | `access_control_sop.md` | ## 4. Mover Procedure | **8 business hours** | Remove previous bundle within 8bh | acs_mover | Yes | — |
| F-ACS-007 | `access_control_sop.md` | ## 4. Mover Procedure | **5 business days** | Dual-bundle max 5 business days | acs_mover | Yes | — |
| F-ACS-008 | `access_control_sop.md` | ## 5. Leaver Procedure | **60 minutes** | Disable login within 60 minutes business hours | acs_leaver | Yes | — |
| F-ACS-009 | `access_control_sop.md` | ## 5. Leaver Procedure | **2 hours** after-hours | Disable login within 2 hours after-hours | acs_leaver | Yes | — |
| F-ACS-010 | `access_control_sop.md` | ## 5. Leaver Procedure | within **3 hours** | Revoke tokens within 3 hours | acs_leaver | Yes | — |
| F-ACS-011 | `access_control_sop.md` | ## 6. Privileged Elevation (JIT) | `jit_prod_write` \| 2 hours | jit_prod_write max 2 hours | acs_jit | Yes | — |
| F-ACS-012 | `access_control_sop.md` | ## 6. Privileged Elevation (JIT) | `jit_breakglass` \| 60 minutes | jit_breakglass max 60 minutes | acs_jit | Yes | — |
| F-ACS-013 | `access_control_sop.md` | ## 6. Privileged Elevation (JIT) | within **24 hours** | Break-glass note within 24 hours | acs_jit | Yes | — |
| F-ACS-014 | `access_control_sop.md` | ## 7. Vendor Access | **21 calendar days** | Vendor access default window 21 calendar days | acs_vendor | Yes | — |
| F-ACS-015 | `access_control_sop.md` | ## 7. Vendor Access | **20 minutes** | Vendor idle timeout 20 minutes | acs_vendor | Yes | — |
| F-ACS-016 | `access_control_sop.md` | ## 8. Audit Sampling | **5%** | Audit samples 5% of JIT weekly | acs_audit | Yes | — |
| F-ACS-017 | `access_control_sop.md` | ## 8. Audit Sampling | **3 business days** | Anomaly tickets due in 3 business days | acs_audit | Yes | — |
| F-ACS-018 | `access_control_sop.md` | ## 9. Contacts | access@novaforge.example | access@novaforge.example | acs_contact | Yes | — |
| F-PRC-001 | `procurement_vendor_policy.md` | ## 2. Vendor Tiers | Under 50,000 | V1 annual spend under $50,000 | prc_tier | Yes | — |
| F-PRC-002 | `procurement_vendor_policy.md` | ## 2. Vendor Tiers | SOC2 summary or equivalent | V3 requires SOC2 summary or equivalent | prc_tier | Yes | — |
| F-PRC-003 | `procurement_vendor_policy.md` | ## 2. Vendor Tiers | **36 months** | V4 on-site audit every 36 months | prc_tier | Yes | — |
| F-PRC-004 | `procurement_vendor_policy.md` | ## 3. Purchase Order Rules | **$200.00** | PO mandatory above $200 | prc_po | Yes | — |
| F-PRC-005 | `procurement_vendor_policy.md` | ## 3. Purchase Order Rules | **5%** quantity or **$75.00** | Over-receipt tolerance 5% or $75 | prc_po | Yes | — |
| F-PRC-006 | `procurement_vendor_policy.md` | ## 3. Purchase Order Rules | **3%** | Price variance >3% needs buyer ack | prc_po | Yes | — |
| F-PRC-007 | `procurement_vendor_policy.md` | ## 3. Purchase Order Rules | `EPO-` | Emergency PO prefix EPO- | prc_po | Yes | — |
| F-PRC-008 | `procurement_vendor_policy.md` | ## 4. ASN and Delivery Windows | Parcel \| 4 hours | Parcel ASN due 4 hours before arrival | prc_asn | Yes | — |
| F-PRC-009 | `procurement_vendor_policy.md` | ## 4. ASN and Delivery Windows | ± 4 hours of appointment | LTL appointment ±4 hours | prc_asn | Yes | — |
| F-PRC-010 | `procurement_vendor_policy.md` | ## 4. ASN and Delivery Windows | ± 2 hours of appointment | FTL appointment ±2 hours | prc_asn | Yes | — |
| F-PRC-011 | `procurement_vendor_policy.md` | ## 4. ASN and Delivery Windows | 6-hour notice | NOSHOW without 6-hour notice | prc_asn | Yes | — |
| F-PRC-012 | `procurement_vendor_policy.md` | ## 5. Vendor Scorecard Metrics | ≥ 92% | On-time inbound ≥92% | prc_score | Yes | — |
| F-PRC-013 | `procurement_vendor_policy.md` | ## 5. Vendor Scorecard Metrics | ≤ 1.5% | Defect rate ≤1.5% | prc_score | Yes | — |
| F-PRC-014 | `procurement_vendor_policy.md` | ## 5. Vendor Scorecard Metrics | ≥ 95% | ASN accuracy ≥95% | prc_score | Yes | — |
| F-PRC-015 | `procurement_vendor_policy.md` | ## 5. Vendor Scorecard Metrics | ≥ 90% | Invoice match first-pass ≥90% | prc_score | Yes | — |
| F-PRC-016 | `procurement_vendor_policy.md` | ## 5. Vendor Scorecard Metrics | **60 calendar days** | PIP lasts 60 calendar days | prc_score | Yes | — |
| F-PRC-017 | `procurement_vendor_policy.md` | ## 6. Corrective Action Procedure | day **30** | PIP checkpoint day 30 | prc_pip | Yes | — |
| F-PRC-018 | `procurement_vendor_policy.md` | ## 6. Corrective Action Procedure | within **24 hours** | Offboard freezes new POs within 24 hours | prc_pip | Yes | — |
| F-PRC-019 | `procurement_vendor_policy.md` | ## 7. Ethical Sourcing Flags | **2 business days** | Trade review SLA 2 business days | prc_trade | Yes | — |
| F-PRC-020 | `procurement_vendor_policy.md` | ## 8. Contacts | procurement@novaforge.example | procurement@novaforge.example | prc_contact | Yes | — |
| F-SRE-001 | `platform_uptime_sla.md` | ## 2. Availability Targets | 99.90% | Checkout uptime 99.90% | sre_avail | Yes | — |
| F-SRE-002 | `platform_uptime_sla.md` | ## 2. Availability Targets | OMS API \| 99.95% | OMS API uptime 99.95% | sre_avail | Yes | — |
| F-SRE-003 | `platform_uptime_sla.md` | ## 2. Availability Targets | Ticket console \| 99.80% | Ticket console uptime 99.80% | sre_avail | Yes | — |
| F-SRE-004 | `platform_uptime_sla.md` | ## 2. Availability Targets | Partner portal \| 99.50% | Partner portal uptime 99.50% | sre_avail | Yes | — |
| F-SRE-005 | `platform_uptime_sla.md` | ## 3. Severity Definitions | SEV-1 \| Checkout or login down for all regions \| 10 minutes \| 60 minutes | SEV-1 ack 10m / mitigate 60m | sre_sev | Yes | — |
| F-SRE-006 | `platform_uptime_sla.md` | ## 3. Severity Definitions | SEV-2 \| Single region or single payment method down \| 20 minutes \| 2 hours | SEV-2 ack 20m / mitigate 2h | sre_sev | Yes | — |
| F-SRE-007 | `platform_uptime_sla.md` | ## 3. Severity Definitions | SEV-3 \| Degraded latency over 3× baseline \| 45 minutes \| 8 hours | SEV-3 ack 45m / mitigate 8h | sre_sev | Yes | — |
| F-SRE-008 | `platform_uptime_sla.md` | ## 4. Customer Communication Cadence | **15 minutes** | Status update within 15 minutes of ack | sre_comms | Yes | — |
| F-SRE-009 | `platform_uptime_sla.md` | ## 4. Customer Communication Cadence | **25 minutes** | Follow-up every 25 minutes until mitigated | sre_comms | Yes | — |
| F-SRE-010 | `platform_uptime_sla.md` | ## 4. Customer Communication Cadence | **5 business days** for SEV-1 | SEV-1 postmortem within 5 business days | sre_comms | Yes | — |
| F-SRE-011 | `platform_uptime_sla.md` | ## 4. Customer Communication Cadence | https://status.novaforge.example | Status page status.novaforge.example | sre_comms | Yes | — |
| F-SRE-012 | `platform_uptime_sla.md` | ## 5. Maintenance Windows | `MW-WEEKLY` \| Tue 06:00–08:00 \| 90 minutes \| 72 hours | MW-WEEKLY notice 72 hours | sre_maint | Yes | — |
| F-SRE-013 | `platform_uptime_sla.md` | ## 5. Maintenance Windows | `MW-MONTHLY` \| First Sun 04:00–07:00 \| 150 minutes \| 5 calendar days | MW-MONTHLY notice 5 calendar days | sre_maint | Yes | — |
| F-SRE-014 | `platform_uptime_sla.md` | ## 5. Maintenance Windows | `MW-EMERGENCY` \| As needed \| 60 minutes | MW-EMERGENCY max 60 minutes | sre_maint | Yes | — |
| F-SRE-015 | `platform_uptime_sla.md` | ## 5. Maintenance Windows | Overlapping `MW-WEEKLY` and `MW-MONTHLY` in the same week is prohibited | No weekly+monthly MW same week | sre_maint | Yes | — |
| F-SRE-016 | `platform_uptime_sla.md` | ## 6. Error Budget Policy | **≥ 75%** | Feature freeze at ≥75% error budget | sre_budget | Yes | — |
| F-SRE-017 | `platform_uptime_sla.md` | ## 6. Error Budget Policy | **≥ 2×** for 1 hour | Burn ≥2× for 1h pages #sre-primary | sre_budget | Yes | — |
| F-SRE-018 | `platform_uptime_sla.md` | ## 7. On-Call | **8 calendar days** | On-call rotation 8 calendar days | sre_oncall | Yes | — |
| F-SRE-019 | `platform_uptime_sla.md` | ## 7. On-Call | **2 hours** before rotation end | Handoff due 2 hours before rotation end | sre_oncall | Yes | — |
| F-SRE-020 | `platform_uptime_sla.md` | ## 7. On-Call | **8 minutes** | Page ack timeout 8 minutes | sre_oncall | Yes | — |
| F-SRE-021 | `platform_uptime_sla.md` | ## 8. Contacts | sre@novaforge.example | sre@novaforge.example | sre_contact | Yes | — |

## Counts by document

| Document | Fact count |
|---|---:|
| `access_control_sop.md` | 18 |
| `account_operations_guide.md` | 21 |
| `carrier_exception_playbook.md` | 17 |
| `finance_credit_memo_policy.md` | 19 |
| `inventory_operations_sop.md` | 24 |
| `order_management_sop.md` | 19 |
| `payment_processing_policy.md` | 23 |
| `platform_uptime_sla.md` | 21 |
| `procurement_vendor_policy.md` | 20 |
| `returns_warehouse_sop.md` | 17 |
| `support_queue_routing.md` | 18 |
| **Total** | **217** |
