# Application Flow Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | Application Flow Specification |
| Project | Internal Payment Workflow System |
| Version | 1.0 |
| Scope | MVP v1 |

---

## Application Structure Overview

1. **Single-page application or multi-page:** Web application. Route-based navigation. No client-side routing complexity beyond defined routes.

2. **Entry point:** Unauthenticated user lands on login route. Authenticated user lands on home route (batches list or pending requests depending on role).

3. **Data flow:** User action triggers API call. Response updates local state. Screen re-renders from state. No business logic in frontend; all validation and state transitions occur server-side.

4. **Session:** Token stored client-side. Token sent in Authorization header for all authenticated requests. On 401, redirect to login route.

---

## Route Registry

| Route | Path | Allowed Roles | Description |
|-------|------|---------------|-------------|
| R1 | /login | Unauthenticated | Login form. |
| R2 | / | CREATOR, APPROVER, VIEWER | Home. Redirects: CREATOR/VIEWER to batches list; APPROVER to pending requests. |
| R3 | /batches | CREATOR, APPROVER, VIEWER | Batches list. |
| R4 | /batches/new | CREATOR | Create batch form. |
| R5 | /batches/:batchId | CREATOR, APPROVER, VIEWER | Batch detail with embedded requests list. |
| R6 | /batches/:batchId/requests/:requestId | CREATOR, APPROVER, VIEWER | Payment request detail. |
| R7 | /requests | APPROVER | Pending requests list (approval queue). |
| R8 | /requests/:requestId | APPROVER | Payment request detail from approval queue. |
| R9 | /audit | CREATOR, APPROVER, VIEWER | Audit log query. |

---

## Role-Based Screen Access Matrix

| Route | CREATOR | APPROVER | VIEWER |
|-------|---------|----------|--------|
| /login | No (redirect if authenticated) | No | No |
| / | Yes | Yes | Yes |
| /batches | Yes | Yes | Yes |
| /batches/new | Yes | No | No |
| /batches/:batchId | Yes | Yes | Yes |
| /batches/:batchId/requests/:requestId | Yes | Yes | Yes |
| /requests | No | Yes | No |
| /requests/:requestId | No | Yes | No |
| /audit | Yes | Yes | Yes |

---

## Screen Definitions

### R1: Login

**Route:** /login  
**Allowed roles:** Unauthenticated only.  
**Data load:** None.  
**Primary actions:** Submit credentials.  
**Navigation targets:** On success, redirect to /. On failure, remain on /login, display error.  
**Mutation actions:** None other than login.  

---

### R2: Home

**Route:** /  
**Allowed roles:** CREATOR, APPROVER, VIEWER.  
**Data load:** GET /api/v1/users/me.  
**Primary actions:** Navigate to batches or pending requests based on role.  
**Navigation targets:** /batches (CREATOR, VIEWER), /requests (APPROVER).  
**Mutation actions:** None.  

---

### R3: Batches List

**Route:** /batches  
**Allowed roles:** CREATOR, APPROVER, VIEWER.  
**Data load:** GET /api/v1/batches with optional status query.  
**Primary actions:** Navigate to batch detail, navigate to create batch (CREATOR only).  
**Navigation targets:** /batches/:batchId, /batches/new.  
**Mutation actions:** None on this screen.  

---

### R4: Create Batch

**Route:** /batches/new  
**Allowed roles:** CREATOR.  
**Data load:** None.  
**Primary actions:** Create batch.  
**Navigation targets:** On success, redirect to /batches/:batchId.  
**Mutation actions:** Create batch.  

---

### R5: Batch Detail

**Route:** /batches/:batchId  
**Allowed roles:** CREATOR, APPROVER, VIEWER.  
**Data load:** GET /api/v1/batches/:batchId.  
**Primary actions:** Submit batch, Cancel batch, Add request, Navigate to request detail.  
**Navigation targets:** /batches/:batchId/requests/:requestId.  
**Mutation actions:** Submit batch, Cancel batch, Add request. Visibility governed by State-Based UI Visibility Rules.  

---

### R6: Payment Request Detail (from batch context)

**Route:** /batches/:batchId/requests/:requestId  
**Allowed roles:** CREATOR, APPROVER, VIEWER.  
**Data load:** GET /api/v1/batches/:batchId/requests/:requestId.  
**Primary actions:** Update request, Upload SOA, Approve, Reject, Mark paid. Navigate back to batch.  
**Navigation targets:** /batches/:batchId.  
**Mutation actions:** Update request, Upload SOA, Approve, Reject, Mark paid. Visibility governed by State-Based UI Visibility Rules.  

---

### R7: Pending Requests List

**Route:** /requests  
**Allowed roles:** APPROVER.  
**Data load:** GET /api/v1/requests with status=PENDING_APPROVAL.  
**Primary actions:** Navigate to request detail.  
**Navigation targets:** /requests/:requestId.  
**Mutation actions:** None on this screen.  

---

### R8: Payment Request Detail (from approval queue)

**Route:** /requests/:requestId  
**Allowed roles:** APPROVER.  
**Data load:** GET /api/v1/batches/:batchId/requests/:requestId (batchId from request data).  
**Primary actions:** Approve, Reject, Mark paid. Navigate back to pending list.  
**Navigation targets:** /requests.  
**Mutation actions:** Approve, Reject, Mark paid. Visibility governed by State-Based UI Visibility Rules.  

---

### R9: Audit Log

**Route:** /audit  
**Allowed roles:** CREATOR, APPROVER, VIEWER.  
**Data load:** GET /api/v1/audit with optional filters.  
**Primary actions:** Apply filters, paginate.  
**Navigation targets:** None (read-only).  
**Mutation actions:** None.  

---

## Action-to-API Mapping Table

| Screen | Action | HTTP Method | API Endpoint | Required Role |
|--------|--------|-------------|--------------|---------------|
| R1 Login | Submit credentials | POST | /api/v1/auth/login | None |
| R1 Login | Logout | POST | /api/v1/auth/logout | Any authenticated |
| R4 Create Batch | Create batch | POST | /api/v1/batches | CREATOR |
| R5 Batch Detail | Submit batch | POST | /api/v1/batches/:batchId/submit | CREATOR |
| R5 Batch Detail | Cancel batch | POST | /api/v1/batches/:batchId/cancel | CREATOR |
| R5 Batch Detail | Add request | POST | /api/v1/batches/:batchId/requests | CREATOR |
| R6 Request Detail | Update request | PATCH | /api/v1/batches/:batchId/requests/:requestId | CREATOR |
| R6 Request Detail | Upload SOA | POST | /api/v1/batches/:batchId/requests/:requestId/soa | CREATOR |
| R6 Request Detail | Approve request | POST | /api/v1/requests/:requestId/approve | APPROVER |
| R6 Request Detail | Reject request | POST | /api/v1/requests/:requestId/reject | APPROVER |
| R6 Request Detail | Mark paid | POST | /api/v1/requests/:requestId/mark-paid | CREATOR or APPROVER |
| R8 Request Detail | Approve request | POST | /api/v1/requests/:requestId/approve | APPROVER |
| R8 Request Detail | Reject request | POST | /api/v1/requests/:requestId/reject | APPROVER |
| R8 Request Detail | Mark paid | POST | /api/v1/requests/:requestId/mark-paid | CREATOR or APPROVER |

---

## State-Based UI Visibility Rules

### Batch-Level Rules

| Batch Status | Submit Button | Cancel Button | Add Request Button |
|--------------|---------------|---------------|---------------------|
| DRAFT | Visible (CREATOR, batch creator) | Visible (CREATOR, batch creator) | Visible (CREATOR, batch creator) |
| SUBMITTED | Hidden | Hidden | Hidden |
| PROCESSING | Hidden | Hidden | Hidden |
| COMPLETED | Hidden | Hidden | Hidden |
| CANCELLED | Hidden | Hidden | Hidden |

**CLOSED batch rule:** When batch status is COMPLETED or CANCELLED, all mutation actions are disabled. No Submit, Cancel, Add Request, Update Request, Upload SOA, Approve, Reject, or Mark Paid buttons are shown or enabled for any request in the batch.

---

### Request-Level Rules (within batch context)

| Request Status | Edit Button | Upload SOA Button | Approve Button | Reject Button | Mark Paid Button |
|----------------|-------------|-------------------|----------------|---------------|------------------|
| DRAFT | Visible (CREATOR, batch creator) | Visible (CREATOR, batch creator) | Hidden | Hidden | Hidden |
| SUBMITTED | Hidden | Hidden | Hidden | Hidden | Hidden |
| PENDING_APPROVAL | Hidden | Hidden | Visible (APPROVER) | Visible (APPROVER) | Hidden |
| APPROVED | Hidden | Hidden | Hidden | Hidden | Visible (CREATOR or APPROVER) |
| REJECTED | Hidden | Hidden | Hidden | Hidden | Hidden |
| PAID | Hidden | Hidden | Hidden | Hidden | Hidden |

**PAID state rule:** When request status is PAID, all mutation actions are disabled. No button may trigger a mutation. The request is read-only.

**REJECTED state rule:** When request status is REJECTED, all mutation actions are disabled. The request is read-only.

---

### Request-Level Rules (approval queue context R8)

| Request Status | Approve Button | Reject Button | Mark Paid Button |
|----------------|----------------|---------------|-------------------|
| PENDING_APPROVAL | Visible | Visible | Hidden |
| APPROVED | Hidden | Hidden | Visible |
| REJECTED | Hidden | Hidden | Hidden |
| PAID | Hidden | Hidden | Hidden |

---

## Error State Handling Rules

1. **Standard error format:** All API error responses conform to {"error": {"code": "...", "message": "...", "details": {}}}. The UI must parse this structure.

2. **Error display:** Display error.message to the user. Do not display error.code or error.details to the user unless specifically intended (e.g. validation field names).

3. **Error code handling:**
   - UNAUTHORIZED (401): Clear token. Redirect to /login.
   - FORBIDDEN (403): Display message. Do not retry. User lacks permission.
   - NOT_FOUND (404): Display message. Offer navigation back to parent route.
   - VALIDATION_ERROR (400): Display message. Highlight invalid fields if details provided.
   - INVALID_STATE (409): Display message. Reload entity. Refresh screen state.
   - PRECONDITION_FAILED (412): Display message. Reload entity.
   - CONFLICT (409): Display message. Reload entity. See Concurrency Handling Behavior.
   - INTERNAL_ERROR (500): Display generic message. Do not expose internal details.

4. **No hidden flows:** Every error path must result in a visible user-visible outcome (message, redirect, or state refresh). No silent failures.

---

## Empty State Handling Rules

1. **Batches list empty:** Display message "No batches yet." Offer "Create batch" button (CREATOR only).

2. **Batch has no requests:** Display message "No payment requests in this batch." Offer "Add request" button when batch is DRAFT and user is CREATOR and batch creator.

3. **Pending requests list empty:** Display message "No pending requests."

4. **Audit log empty:** Display message "No audit entries match your filters."

5. **SOA list empty:** Display message "No Statement of Account documents." Offer "Upload SOA" when request is DRAFT and user is CREATOR and batch creator.

---

## Navigation Constraints

1. **Maximum navigation depth:** 4. Root (/) -> Level 1 (e.g. /batches) -> Level 2 (e.g. /batches/:batchId) -> Level 3 (e.g. /batches/:batchId/requests/:requestId). No deeper nesting.

2. **Back navigation:** Every screen at depth 2 or greater must provide explicit back navigation to the parent route. No browser-back-only dependency.

3. **Role-based redirect:** When an authenticated user navigates to a route they lack permission for, redirect to /. Do not display the forbidden route.

4. **Orphan prevention:** When navigating to /batches/:batchId/requests/:requestId, the batchId must match the request's batch. If mismatch, redirect to /batches/:batchId.

---

## Concurrency Handling Behavior

1. **Conflict detection:** When a mutation returns 409 CONFLICT or INVALID_STATE, the server indicates a concurrent modification or stale state.

2. **Reload behavior:** On 409 CONFLICT or INVALID_STATE, the client must: (a) discard local mutations; (b) re-fetch the affected entity (GET batch or GET request); (c) refresh the screen with the fetched data; (d) display a message indicating the operation could not complete due to a conflict.

3. **No retry without user action:** Do not automatically retry the failed mutation. The user must re-initiate the action after the screen has been refreshed.

4. **Optimistic locking:** The UI does not perform optimistic locking. All state is derived from server responses after mutations.

---

## UI Determinism Rules

1. **No client-side business logic:** The UI does not validate state transitions, permission rules, or domain invariants. The server is the source of truth. The UI displays server state and sends user intent to the server.

2. **State from server:** After every mutation, the UI updates its state from the mutation response or from a subsequent GET. The UI does not infer state changes locally.

3. **Button visibility is deterministic:** Button visibility is computed from: (a) user role; (b) batch status; (c) request status; (d) ownership (batch creator). The same inputs always produce the same visibility.

4. **No hidden flows:** Every user action has a defined outcome. No action may result in an undefined or unreachable state.

---

## Application Flow Freeze Declaration

This application flow specification is frozen for MVP v1. No route, action, visibility rule, error handling rule, or navigation constraint may be added, removed, or altered without a formal change control process and document revision.

**Explicit enforcement:**

1. CLOSED batch (COMPLETED or CANCELLED) must disable all mutation actions.
2. PAID state must disable all mutation actions.
3. REJECTED state must disable all mutation actions.
4. Every action must map to an API endpoint defined in the API contract.
5. Error handling must reference the standardized error format.
6. Concurrency conflict (409) must trigger reload behavior.

**HOLD to RESUBMIT path (out of scope for MVP):** HOLD and RESUBMIT are not defined in the frozen domain model. When HOLD state is added, the RESUBMIT path will transition a request from HOLD back to DRAFT or SUBMITTED for re-approval. This path is not implemented in MVP v1.
