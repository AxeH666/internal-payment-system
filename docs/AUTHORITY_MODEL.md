# Authority Model

**Project:** Internal Payment Workflow System  
**Phase 2 baseline.** Defines explicit ADMIN powers and role × capability matrix.  
**Complements:** [05_SECURITY_MODEL.md](05_SECURITY_MODEL.md)

---

## Roles

| Role    | Description |
|---------|-------------|
| VIEWER  | Read-only access to batches, requests, audit log. No mutations. |
| CREATOR | Create batches and payment requests; submit/cancel batches; update requests; upload SOA. Ownership enforced: non-ADMIN can only act on batches they created. |
| APPROVER | View pending requests; approve or reject requests; mark requests as paid. |
| ADMIN   | All of the above plus: ledger CRUD (clients, sites, vendors, subcontractors, vendor types, scopes); user creation (non-ADMIN only). ADMIN cannot be created via API. |

---

## ADMIN powers (explicit)

- **Ledger:** Create and update clients, sites, vendors, subcontractors, vendor types, subcontractor scopes. Only ADMIN can perform these operations (enforced in views and services).
- **Payments (batch creator actions):** ADMIN can act as batch creator on any batch (add request, submit batch, cancel batch, update request, upload SOA) without ownership check. Service layer treats ADMIN as bypass for “batch creator” ownership.
- **Payments (approval actions):** ADMIN can approve requests, reject requests, and mark requests as paid (same as APPROVER). Enforced in both view (IsApprover / IsCreatorOrApprover) and service (role in APPROVER, ADMIN for approve/reject; CREATOR, APPROVER, ADMIN for mark_paid).
- **Users:** Only ADMIN can create users via POST /api/v1/users. Created users may have role CREATOR, APPROVER, or VIEWER only. Serializer rejects role=ADMIN with “Cannot create ADMIN users via API.”
- **ADMIN creation:** There is no API or UI to create or upgrade to ADMIN. ADMIN is created only via CLI/shell (e.g. `create_admin_user()` in `apps.users.services`). See [ADMIN_CREATION_RUNBOOK.md](ADMIN_CREATION_RUNBOOK.md) (Phase 2).

---

## Authority matrix (role × capability)

| Capability              | VIEWER | CREATOR | APPROVER | ADMIN |
|-------------------------|--------|---------|----------|-------|
| List batches / requests | Yes    | Yes     | Yes      | Yes   |
| Create batch            | No     | Yes     | No       | Yes   |
| Add request to batch    | No     | Owner   | No       | Yes   |
| Update request          | No     | Owner   | No       | Yes   |
| Submit batch            | No     | Owner   | No       | Yes   |
| Cancel batch            | No     | Owner   | No       | Yes   |
| Upload SOA              | No     | Owner   | No       | Yes   |
| List pending requests   | No     | No      | Yes      | Yes   |
| Approve request         | No     | No      | Yes      | Yes   |
| Reject request          | No     | No      | Yes      | Yes   |
| Mark request paid       | No     | Yes     | Yes      | Yes   |
| Ledger CRUD             | No     | No      | No       | Yes   |
| Audit log read          | Yes    | Yes     | Yes      | Yes   |
| Create user (non-ADMIN) | No     | No      | No       | Yes   |

*Owner* = batch creator only (for non-ADMIN CREATOR). ADMIN can perform all creator actions on any batch.

---

## No privilege escalation

- Role is never accepted from request body for authorization; it is read from the authenticated user (JWT/subject).
- User creation API accepts `role` in body but serializer rejects `ADMIN`; only CREATOR, APPROVER, VIEWER can be assigned.
- No endpoint allows updating an existing user’s role to ADMIN (no such PATCH/PUT in scope).
- All mutation endpoints enforce role or ownership in both view and service layer.
