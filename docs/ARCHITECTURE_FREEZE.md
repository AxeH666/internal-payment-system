# Architecture Freeze Declaration

**Document Type:** Internal Engineering Contract  
**Architecture Version:** v0.1.0  
**Freeze Date:** 2025-02-12  
**Status:** Enforced

---

## 1. Scope

Phase 1 (Sub-phases 1.1 through 1.5) is hereby declared frozen. All specification artifacts produced within Phase 1 are immutable under this contract.

---

## 2. Mandatory Documentation Files

The following ten documentation files constitute the frozen specification corpus:

| # | Document |
|---|----------|
| 1 | 01_PRD.md |
| 2 | 02_DOMAIN_MODEL.md |
| 3 | 03_STATE_MACHINE.md |
| 4 | 04_API_CONTRACT.md |
| 5 | 05_SECURITY_MODEL.md |
| 6 | 06_BACKEND_STRUCTURE.md |
| 7 | 07_APP_FLOW.md |
| 8 | 08_FRONTEND_GUIDELINES.md |
| 9 | 09_TECH_STACK.md |
| 10 | 10_IMPLEMENTATION_PLAN.md |

All documents reside in the `docs/` directory.

---

## 3. Change Control

The following changes require an architecture version bump before implementation:

- **Entity changes:** No modifications to domain entities, models, or their attributes are permitted without an architecture version bump.

- **State machine changes:** No modifications to state definitions, transitions, or transition rules are permitted without an architecture version bump.

- **API contract changes:** No modifications to endpoints, request/response schemas, or authentication/authorization requirements are permitted without an architecture version bump.

- **Security model weakening:** No weakening of the security model is permitted, regardless of version. Security model strengthening may proceed without version bump subject to review.

---

## 4. Backend Implementation Requirements

Backend implementation must strictly adhere to the following specifications:

- 02_DOMAIN_MODEL.md  
- 03_STATE_MACHINE.md  
- 04_API_CONTRACT.md  
- 05_SECURITY_MODEL.md  

Deviations from these documents are prohibited. Implementation must conform to the intent and structure defined therein.

---

## 5. Enforcement

This contract is binding upon all engineering personnel contributing to the Internal Payment Workflow System. Violations shall be remediated before merge. Architecture version bumps require formal review and approval.

---

*Document issued under Architecture Governor authority.*

---

## 6. API Contract v2.0 Freeze

**Freeze Date:** 2026-03-01
**Contract Version:** v2.0
**Git Tag:** v1.0.0-api-freeze
**Previous Contract Version:** v1.0 (2025-02-11)

### 6.1 Scope

The API contract specification (`04_API_CONTRACT.md`) has been updated to v2.0 and is hereby frozen. All endpoints, schemas, permissions, and versioning policy documented in v2.0 are immutable under this contract.

### 6.2 Changes from v1.0 to v2.0

1. ADMIN role added to all role tables and permission definitions.
2. `mark-paid` permission corrected from CREATOR/APPROVER to ADMIN-only.
3. `POST /api/v1/users` endpoint added — ADMIN-only user creation.
4. Phase 2 ledger fields added to PaymentRequest response schema: entityType, vendorId, subcontractorId, siteId, baseAmount, extraAmount, totalAmount, entityName, siteCode.
5. Reference Data section added — all 10 ledger endpoints fully documented.
6. `GET .../soa/{versionId}/download` endpoint added — file binary download, audits SOA_DOWNLOADED.
7. `GET /api/v1/batches/{batchId}/soa-export` endpoint added — batch PDF/Excel export.
8. API Versioning Policy section added — v1 stability guarantees and breaking change policy.
9. Idempotency-Key requirement clarified for all mutation endpoints.
10. Audit log entityType filter extended to include ledger entity types.

### 6.3 Enforcement

All v1 stability guarantees defined in Section H of `04_API_CONTRACT.md` are binding:

- No response fields may be renamed or removed in v1.
- No permissions may be broadened in v1.
- No URL patterns may change in v1.
- Breaking changes require `/api/v2/` and a new architecture version bump.

### 6.4 docs_check.py Update

`FORBIDDEN_TERMS` in `docs_check.py` was updated to remove `"ledger"` as ledger endpoints are now in scope and documented in the frozen contract.

---

*API Contract v2.0 freeze issued under Architecture Governor authority.*
