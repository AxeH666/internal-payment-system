# STEP 2 — Authority Model Clarification

**Phase 2 Controlled Execution Plan — Verification Artifact**

**Date:** 2025-02-20

---

## 1. mark_paid ADMIN inconsistency — resolution

**Decision:** **(A) Align service with view.**

**Change location:** `backend/apps/payments/services.py`, in `mark_paid()`, role check (lines 977–981).

**Change:** Role check updated from `("CREATOR", "APPROVER")` to `("CREATOR", "APPROVER", "ADMIN")` so ADMIN can mark requests as paid at the service layer. The view already allowed ADMIN via `IsCreatorOrApprover`; the service previously raised `PermissionDeniedError` for ADMIN. Behavior is now consistent with `approve_request` and `reject_request`, which allow ADMIN in both view and service.

**Code (after):**

```python
# Check role (ADMIN can mark paid, consistent with approve/reject)
if actor.role not in ("CREATOR", "APPROVER", "ADMIN"):
    raise PermissionDeniedError(
        "Only CREATOR, APPROVER, or ADMIN can mark requests as paid"
    )
```

---

## 2. Documentation — ADMIN powers and authority matrix

**Document:** [docs/AUTHORITY_MODEL.md](docs/AUTHORITY_MODEL.md)

**Contents (summary):**

- **ADMIN powers:** Ledger CRUD; act as batch creator on any batch (add request, submit, cancel, update request, upload SOA); approve, reject, mark_paid; create users (non-ADMIN only); ADMIN cannot be created via API; ADMIN created via CLI/shell only.
- **Authority matrix:** Role × capability table for VIEWER, CREATOR, APPROVER, ADMIN (list batches, create batch, add/update request, submit/cancel, upload SOA, approve/reject/mark_paid, ledger CRUD, audit read, create user).
- **No privilege escalation:** Role from authenticated user only; serializer rejects ADMIN on user create; no endpoint upgrades user to ADMIN.

---

## 3. Privilege escalation confirmation

- **User create:** `backend/apps/users/serializers.py` — `validate_role` raises `ValidationError("Cannot create ADMIN users via API")` when `value == Role.ADMIN`. Confirmed.
- **No user update endpoint:** No PATCH/PUT for user role in scope. Confirmed.
- **View layer:** No view allows setting or upgrading to ADMIN. Confirmed.

No privilege escalation path identified.

---

## 4. Final declaration

**PASS**

mark_paid behavior is consistent between view and service. ADMIN powers and authority matrix are documented in `docs/AUTHORITY_MODEL.md`. No privilege escalation path. Artifact complete.
