# Security Model Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | Security Model Specification |
| Project | Internal Payment Workflow System |
| Version | 1.0 |
| Scope | MVP v1 |
| Classification | Internal Use |

---

## Security Objectives

1. **Confidentiality:** Ensure that payment data, beneficiary information, and audit records are accessible only to authorized users.

2. **Integrity:** Ensure that no unauthorized modification of payment requests, batches, approval records, or audit log entries occurs.

3. **Availability:** Ensure that the system remains operational within defined business hours for authorized internal users.

4. **Accountability:** Ensure that every state-changing operation is attributable to an authenticated user and recorded in the audit log.

5. **Defense in depth:** Ensure that authentication, authorization, and data protection layers operate independently; failure of one layer does not bypass others.

---

## Threat Model Scope

**In scope:**

1. Unauthorized access by internal users lacking required role.
2. Privilege escalation via client-supplied role or permission claims.
3. Concurrent modification leading to inconsistent state or lost updates.
4. Information leakage via error messages, stack traces, or logs.
5. Credential theft and token reuse.
6. Man-in-the-middle interception of traffic.

**Out of scope:**

1. External attackers (system is internal network only).
2. Physical security of data center or network infrastructure.
3. Insider threat beyond role-based access (e.g. malicious admin).
4. Denial-of-service attacks.
5. Advanced persistent threats.

---

## Authentication Model

1. **Mechanism:** Username and password presented to the authentication endpoint. The server validates credentials against the authoritative user store and issues tokens.

2. **JWT access token:** Upon successful authentication, the server issues a signed JWT access token. The token contains: subject (user identifier), role (CREATOR, APPROVER, or VIEWER), issued-at timestamp, expiration timestamp. The token is signed with a server-held secret. The client presents the token in the Authorization header as Bearer &lt;token&gt;.

3. **Token claims:** The access token must include at minimum: sub (user id), role (user role), iat (issued at), exp (expiration). No sensitive data (passwords, beneficiary details) may be stored in token claims.

4. **Storage:** The access token is stored client-side. The implementation must not store the token in a location accessible to other origins (e.g. no shared localStorage across domains).

5. **Transmission:** Tokens are transmitted only over HTTPS. Tokens must not appear in URLs, query parameters, or referrer headers.

---

## Token Lifecycle Management

1. **Access token expiry:** Access token lifetime must not exceed 15 minutes. Default recommended: 15 minutes.

2. **Refresh token:** The server issues a refresh token upon successful authentication. Refresh token lifetime must not exceed 7 days. Default recommended: 7 days.

3. **Refresh token rotation:** When the client presents a valid refresh token to obtain a new access token (and optionally a new refresh token), the server must invalidate the presented refresh token. A new refresh token may be issued. The old refresh token must not be reusable.

4. **Token invalidation on logout:** When the user logs out, the server must invalidate the current refresh token and record the access token revocation (or its expiry window) so that the access token cannot be used after logout. Revocation mechanism is implementation-defined (e.g. token blocklist, short expiry with logout-timestamp check).

5. **Token invalidation on password change:** When a user password is changed, all refresh tokens for that user must be invalidated. Pending access tokens remain valid until expiry.

6. **Invalid token handling:** Requests with missing, malformed, or expired tokens receive 401 Unauthorized. The response must not disclose whether the token was malformed or expired.

---

## Authorization Model

1. **Role source:** User role (CREATOR, APPROVER, VIEWER) is stored in the authoritative user store and asserted in the access token. The role is never read from request body, query parameters, headers, or any client-supplied payload.

2. **Server-side enforcement:** Every endpoint that performs a mutation or returns sensitive data must validate the authenticated user role against the required role for that endpoint. Validation occurs on the server before any business logic executes.

3. **No frontend trust:** The frontend must not be trusted for authorization decisions. The frontend may hide or disable UI elements based on role, but the server must enforce permission regardless of what the client sends.

4. **Role definitions:**
   - CREATOR: May create batches, add requests, update draft requests, upload SOA, submit batches, cancel draft batches, mark approved requests as paid. May view batches, requests, and audit log.
   - APPROVER: May approve or reject pending requests. May view batches, requests, and audit log.
   - VIEWER: May view batches, requests, approval records, and audit log only. No mutations.

5. **Resource ownership:** Batch creation and submission require that the actor is the batch creator. SOA upload requires that the actor is the creator of the payment request. The server validates ownership by comparing the authenticated user identifier to the Created By field of the resource.

---

## Permission Enforcement Rules

1. **Per-endpoint validation:** Each endpoint defines required role(s). Before executing the handler, the server must: (a) authenticate the request; (b) extract the user identifier and role from the token; (c) verify the role is in the allowed set for the endpoint; (d) verify resource ownership when applicable.

2. **Authorization failure:** When the user lacks the required role, the server returns 403 Forbidden. The response body must use the standard error format. The message must not disclose which role was required.

3. **Not-found vs forbidden:** When the user lacks permission to access a resource that exists, return 403 Forbidden. When the resource does not exist, return 404 Not Found. Do not leak existence of resources the user cannot access.

4. **Precondition validation:** Permission validation occurs before any precondition check (e.g. entity state). A user who lacks permission must not receive information about whether preconditions would have passed.

---

## SuperAdmin Override Controls

1. **Definition:** SuperAdmin is a reserved role with elevated privileges for system administration (e.g. user management, emergency recovery). SuperAdmin is not used for payment workflow operations.

2. **Override actions:** When SuperAdmin performs an override action (e.g. impersonation, manual state correction), the action must be logged in the system log with: actor identifier, action type, affected resource, timestamp, reason (if provided).

3. **No override without logging:** No SuperAdmin override may occur without a corresponding system log entry. The log entry must be written atomically with the override operation.

4. **Audit log:** Override actions that affect domain state (e.g. manual state change) must also create an audit log entry with actor set to the SuperAdmin user. The audit log entry must indicate that the action was an override.

---

## Concurrency & Transaction Integrity

1. **Atomic transaction requirement:** Every mutation that spans multiple persistent writes (e.g. batch submission updating batch and all payment requests) must execute within a single database transaction. The transaction must commit atomically or roll back entirely. No partial writes are permitted.

2. **Row-level locking requirement:** Before modifying a PaymentRequest or PaymentBatch, the server must acquire an exclusive row-level lock on the entity. The lock must be held until the transaction commits. Lock ordering must be consistent (e.g. batch before requests, by identifier) to prevent deadlock.

3. **Optimistic locking:** When optimistic locking is used (e.g. version field), the server must reject the request with 409 Conflict if the version has changed since the client last read the resource. No silent overwrite.

4. **Idempotency:** Mutations that support idempotency keys must return the original result when the key is reused. No duplicate side effects.

---

## Data Exposure Controls

1. **Logs:** No sensitive data may be written to logs. The following must not appear in any log: passwords, tokens, full beneficiary account numbers, full beneficiary names (use redaction or hash for debugging when necessary).

2. **Stack traces:** Stack traces, exception class names, file paths, and line numbers must not be returned to the client in any response. Production error responses must use the standard error format with a generic message.

3. **Error details:** The error.details field in the standard error response may contain field names or constraint identifiers. It must not contain internal implementation details, SQL fragments, or file paths.

4. **Response filtering:** When returning lists, the server must filter results by the authenticated user permission. A Viewer must not receive data that only Approvers or Creators may access.

---

## Error Handling & Information Leakage Controls

1. **Standard error response structure:**

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

2. **Production behavior:** In production, the message must be a generic description suitable for display to the user. The message must not vary based on whether the failure was authentication, authorization, or validation.

3. **No internal detail leakage:** The following must never appear in client responses: database error messages, stack traces, server hostnames, internal service names, configuration values, or version strings.

4. **500 handling:** For unrecoverable server errors, the server returns 500 Internal Server Error with a generic message. The full error is logged server-side only. The client receives only the standard error structure with code INTERNAL_ERROR.

---

## Logging & Monitoring Controls

1. **Audit logs (business):** Immutable chronological record of domain events. Each entry contains: event type, actor identifier, entity type, entity identifier, previous state, new state, timestamp. Audit logs are append-only. No update or delete operations. Audit logs are used for compliance and traceability.

2. **System logs (technical):** Infrastructure and application logs for debugging and monitoring. Contains: request identifiers, endpoint, status code, duration, error type (no sensitive data). System logs may be rotated and retained per organizational policy.

3. **Separation:** Audit log entries are written to a dedicated store. System logs are written to a separate sink. The two must not be conflated.

4. **Sensitive data:** Neither audit logs nor system logs may contain passwords, tokens, or unredacted beneficiary account numbers. Audit logs may contain beneficiary names and amounts for traceability; redaction policy is organizational.

---

## Deployment Hardening Requirements

1. **HTTPS requirement:** All client-server communication must use TLS 1.2 or higher. HTTP must not be accepted in production. Redirect HTTP to HTTPS or fail the connection.

2. **Environment variables:** Secrets (database credentials, JWT signing key, external service keys) must be supplied via environment variables or a secure secret store. Secrets must not be hardcoded or committed to version control.

3. **Debug disabled in production:** Debug mode, verbose error pages, and development-only middleware must be disabled in production. The production build must not include debug symbols or source maps in served assets.

4. **Network:** The application must be accessible only from the internal network or via VPN. No public internet exposure. Firewall rules must restrict inbound connections to authorized sources.

---

## Backup & Recovery Requirements

1. **Frequency:** Database backups must be performed at least daily. Transaction logs or incremental backups must be retained to support point-in-time recovery. Retention period is defined by organizational policy.

2. **Restore verification requirement:** Restore procedures must be tested at least quarterly. A successful restore verification must confirm: database integrity, audit log continuity, and application startup against restored data.

3. **Audit log backup:** The audit log store must be included in backup procedures. Audit log integrity must be preserved (no truncation or partial backup).

---

## Security Invariants

1. **SI-1:** Role is never trusted from client payload. The server must derive user role exclusively from the authenticated session or token, which is validated against the authoritative user store.

2. **SI-2:** No mutation is allowed without permission validation. Every mutation endpoint must validate the authenticated user role and resource ownership before executing any state change.

3. **SI-3:** No partial transaction writes are permitted. Multi-entity mutations must commit atomically or roll back entirely.

4. **SI-4:** No audit entry deletions are permitted. The audit log is append-only. No update or delete operations apply to audit records.

5. **SI-5:** No override occurs without logging. Every SuperAdmin override action must produce a system log entry and, when domain state is affected, an audit log entry.

6. **SI-6:** Tokens are transmitted only over HTTPS. No token may appear in URLs or non-secure channels.

7. **SI-7:** Passwords are never stored in plaintext. Passwords must be hashed with a suitable algorithm (e.g. bcrypt, Argon2) before storage.

8. **SI-8:** The JWT signing key is never exposed to the client. The key is held server-side only.

---

## Security Freeze Declaration

This security model specification is frozen for MVP v1. No objective, threat, authentication rule, authorization rule, invariant, or hardening requirement may be added, removed, or altered without a formal change control process and document revision.
