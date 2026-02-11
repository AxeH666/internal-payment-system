# Frontend Guidelines Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | Frontend Guidelines Specification |
| Project | Internal Payment Workflow System |
| Version | 1.0 |
| Scope | MVP v1 |

---

## Frontend Architecture Principles

1. **Policy:** No business logic in frontend.

2. **Policy:** No state transitions defined client-side. All state transitions are validated and executed by the backend. The frontend displays server state and sends user intent to the API.

3. **Policy:** UI disables CLOSED batch mutation actions. When batch status is COMPLETED or CANCELLED, all mutation buttons (Submit, Cancel, Add Request, Update Request, Upload SOA, Approve, Reject, Mark Paid) are hidden or disabled.

4. **Policy:** UI disables PAID mutation actions. When payment request status is PAID, all mutation buttons are hidden or disabled. The request is read-only.

5. The frontend is a thin presentation layer. All validation, permission checks, and state machine enforcement occur server-side. The frontend derives display state from API responses only.

---

## Error Rendering Rules

1. **Policy:** Error rendering is standardized. All API error responses conform to the format {"error": {"code": "...", "message": "...", "details": {}}}.

2. The UI must parse the error structure and display error.message to the user. Do not display error.code or error.details unless specifically intended (e.g. validation field names).

3. Error code handling: 401 redirects to login; 403 displays permission message; 404 displays not-found message with navigation option; 400 displays validation message; 409 triggers reload behavior. No stack traces or internal details are displayed.

---

## Concurrency Conflict UI Handling

1. **Policy:** Concurrency conflict requires data reload. When the API returns 409 CONFLICT or INVALID_STATE, the UI must discard local mutations, re-fetch the affected entity, refresh the screen with the fetched data, and display a message indicating the operation could not complete due to a conflict.

2. No automatic retry. The user must re-initiate the action after the screen has been refreshed.

3. All state is derived from server responses. The UI does not perform optimistic locking.

---

## Styling and Branding

1. **Policy:** No visual styling specifics included. This document does not specify colors, fonts, spacing, or branding. Implementations apply organizational design standards separately.

---

## Frontend Guidelines Freeze Declaration

This frontend guidelines specification is frozen for MVP v1. No principle, policy, or rule may be added, removed, or altered without a formal change control process and document revision.
