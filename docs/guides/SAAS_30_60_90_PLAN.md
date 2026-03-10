# SaaS 30/60/90 Plan

## 30 Days: Foundation and Risk Control (Phase 1)
- Deliver subscription and entitlement primitives.
- Enforce authentication hardening and permission boundaries for admin actions.
- Establish baseline observability and operational alerts.
- Define production release checklist and rollback SOP.

### Phase 1 In-Sprint Implementations Started
- Added backend subscription primitives on `User`:
  - `subscription_plan`, `subscription_status`, `trial_ends_at`, `plan_expires_at`
- Added entitlement policy engine:
  - `backend/modules/entitlements.py`
  - plan catalog (`starter`, `growth`, `professional`)
  - feature map and active/trial state resolution
- Added user/admin subscription endpoints:
  - `GET /api/v1/auth/entitlements`
  - `PATCH /api/v1/auth/entitlements/{user_id}` (admin)
- Updated registration defaults:
  - new users and practitioners now start on `starter` trial with 14-day trial end.
- Added test coverage:
  - `backend/tests/test_saas_entitlements.py`

### Remaining 30-Day Tasks
- Integrate entitlement checks into paid features (advanced analytics, API access, team management).
- Add subscription events/audit trail for plan changes.
- Add Stripe/Razorpay recurring billing abstraction and webhook signature verification.
- Add dunning states (`past_due`, `grace_period`) workflow.
- Add admin billing operations dashboard.

## 60 Days: Commercial Readiness
- Launch plan checkout and customer billing portal.
- Add invoice and tax/GST support with downloadable receipts.
- Add usage metering + limits enforcement for high-traffic features.
- Introduce organization/team model and role-based workspace access.
- Add customer support tools (account lookup, plan status, payment history).

## 90 Days: Scale and Compliance
- Build DR and backup restore drills with documented RTO/RPO.
- SOC2-style evidence collection pipeline and security control attestations.
- Full SLOs and error-budget driven incident process.
- Mature CI/CD gates: SAST, dependency scans, container scans, policy checks.
- Harden multi-tenant data isolation and introduce tenant-level analytics.

## Exit Criteria for "Full SaaS"
- Self-serve paid onboarding and plan management works end-to-end.
- Entitlements consistently enforced across backend and frontend.
- Billing and finance reconciliation are reliable and auditable.
- Compliance/security controls are operationally monitored.
- Platform can scale and recover with tested runbooks.
