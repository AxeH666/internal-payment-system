# API Contract Specification

**Project:** Internal Payment Workflow System (MVP v1)
**Document Version:** 2.0
**Scope:** Single company, internal web-only, MVP
**Last Updated:** 2026-03-01

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | API Contract Specification |
| Project | Internal Payment Workflow System |
| Version | 2.0 |
| Scope | MVP v1 |
| Base Path | /api/v1 |

---

## General API Principles

1. All endpoints use JSON for request and response bodies. Content-Type is application/json.
2. All dates and timestamps use ISO 8601 format (e.g. 2026-03-01T14:30:00Z).
3. All identifiers are opaque strings. The implementation defines the format (UUID).
4. All mutations are task-based. No generic create, update, or delete endpoints. Mutations correspond to domain actions (submit, approve, reject, mark-paid).
5. No endpoint may trigger an illegal state transition. Preconditions are enforced before any state change.
6. Pagination uses limit and offset query parameters. Default limit is 50. Maximum limit is 100.
7. All mutation endpoints require an `Idempotency-Key` header. The server enforces uniqueness per key and operation.

---

## Authentication Requirements

1. All endpoints except the Authentication group require a valid JWT bearer token.
2. The server returns 401 Unauthorized when no valid token is presented.
3. The server returns 403 Forbidden when the token is valid but the user lacks the required role.
4. The authenticated user identity and role are derived from the JWT token. Role is never read from the request body or query parameters.
5. Token lifetime is implementation-defined. Refresh tokens may be blacklisted on logout.

---

## Roles

| Role | Description |
|------|-------------|
| CREATOR | Creates and manages payment batches and requests. |
| APPROVER | Reviews and approves or rejects payment requests. |
| VIEWER | Read-only access to all resources. |
| ADMIN | Full access. Can create users, manage reference data, and mark requests as paid. Supersedes all other roles. |

---

## Standard Response Format

### Success Response (Single Resource)

```json
{
  "data": { ... }
}
```

### Success Response (List)

```json
{
  "data": [ ... ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

### Success Response (Mutation)

```json
{
  "data": { ... }
}
```

---

## Standard Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

### Standard Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid authentication. |
| FORBIDDEN | 403 | Authenticated user lacks required role. |
| NOT_FOUND | 404 | Requested resource does not exist. |
| VALIDATION_ERROR | 400 | Request body or parameters fail validation. |
| INVALID_STATE | 409 | Entity is not in the required state for the operation. |
| PRECONDITION_FAILED | 412 | One or more preconditions are not satisfied. |
| CONFLICT | 409 | Concurrent modification, duplicate operation, or duplicate name. |
| INTERNAL_ERROR | 500 | Unrecoverable server error. |

---

## Idempotency

All mutation endpoints (POST, PATCH) require an `Idempotency-Key` header. The server stores the key and associates it with the operation result. If the same key is submitted again for the same operation, the server returns the original result without re-executing the operation. If the same key is submitted with a different request body, the server returns 409 CONFLICT.

Idempotency keys are scoped per operation. The same key value may be used for different operations (e.g. one key for create, a different key for approve).

Read-only endpoints (GET) do not require an Idempotency-Key.

---

## Endpoint Definitions

### Authentication

#### Authenticate

**HTTP Method:** POST
**URL Pattern:** /api/v1/auth/login
**Required Role:** None (unauthenticated)
**Required Current State:** N/A

**Request Body Schema:**

```json
{
  "username": "string",
  "password": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | yes | User login identifier. |
| password | string | yes | User password. |

**Success Response Schema:**

```json
{
  "data": {
    "token": "string",
    "user": {
      "id": "string",
      "username": "string",
      "displayName": "string",
      "role": "CREATOR"
    }
  }
}
```

| Field | Description |
|-------|-------------|
| token | JWT bearer token for subsequent requests. |
| user.id | User identifier. |
| user.username | User login identifier. |
| user.displayName | Human-readable name. |
| user.role | One of CREATOR, APPROVER, VIEWER, ADMIN. |

**Possible Error Codes:** UNAUTHORIZED (invalid credentials), VALIDATION_ERROR (missing username or password).

**Side Effects:** JWT token issued.

**Idempotency Rules:** N/A. Repeated calls with same credentials produce new tokens.

**Concurrency Handling Requirements:** None.

---

#### Logout

**HTTP Method:** POST
**URL Pattern:** /api/v1/auth/logout
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Request Body Schema:**

```json
{
  "refresh_token": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh_token | string | no | Refresh token to blacklist. |

**Success Response Schema:**

```json
{
  "data": {
    "success": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** Refresh token blacklisted if provided.

**Idempotency Rules:** Multiple logout calls return success. No error if token already blacklisted.

**Concurrency Handling Requirements:** None.

---

### Users

#### Get Current User

**HTTP Method:** GET
**URL Pattern:** /api/v1/users/me
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "username": "string",
    "displayName": "string",
    "role": "CREATOR"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### List Users

**HTTP Method:** GET
**URL Pattern:** /api/v1/users
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "username": "string",
      "displayName": "string",
      "role": "CREATOR"
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Create User

**HTTP Method:** POST
**URL Pattern:** /api/v1/users
**Required Role:** ADMIN
**Required Current State:** N/A

This is an internal administrative endpoint. It is not a public registration or onboarding endpoint. Only ADMIN users may create accounts.

**Request Body Schema:**

```json
{
  "username": "string",
  "password": "string",
  "displayName": "string",
  "role": "CREATOR"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | yes | Unique login identifier. Non-empty. |
| password | string | yes | User password. Non-empty. |
| displayName | string | yes | Human-readable name. Non-empty. |
| role | string | yes | One of CREATOR, APPROVER, VIEWER, ADMIN. |

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "username": "string",
    "displayName": "string",
    "role": "CREATOR"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR (missing or invalid fields), CONFLICT (username already exists).

**Side Effects:** User account created.

**Idempotency Rules:** Idempotency-Key header required. Duplicate key returns original created user.

**Concurrency Handling Requirements:** None (unique constraint on username enforced at DB level).

**Preconditions:** Actor has role ADMIN.

---

### Reference Data

Reference data entities (clients, sites, vendors, subcontractors) are shared across all modules. They are managed by ADMIN users and referenced by payment requests.

#### List Clients

**HTTP Method:** GET
**URL Pattern:** /api/v1/ledger/clients
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "isActive": true
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Create Client

**HTTP Method:** POST
**URL Pattern:** /api/v1/ledger/clients
**Required Role:** ADMIN
**Required Current State:** N/A

**Request Body Schema:**

```json
{
  "name": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Unique client name. Non-empty. |

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "name": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR, CONFLICT (duplicate name).

**Side Effects:** Client created. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Name is non-empty and unique.

---

#### Update Client

**HTTP Method:** PATCH
**URL Pattern:** /api/v1/ledger/clients/{clientId}
**Required Role:** ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| clientId | string | Client identifier. |

**Request Body Schema:**

```json
{
  "name": "string",
  "isActive": true
}
```

All fields optional. Provided fields are updated. Omitted fields are unchanged.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "name": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, VALIDATION_ERROR, CONFLICT (duplicate name).

**Side Effects:** Client updated. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Client exists.

---

#### List Sites

**HTTP Method:** GET
**URL Pattern:** /api/v1/ledger/sites
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| clientId | string | no | Filter by client identifier. |
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "code": "string",
      "name": "string",
      "clientId": "string",
      "isActive": true
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Create Site

**HTTP Method:** POST
**URL Pattern:** /api/v1/ledger/sites
**Required Role:** ADMIN
**Required Current State:** N/A

**Request Body Schema:**

```json
{
  "code": "string",
  "name": "string",
  "clientId": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| code | string | yes | Unique site code. Non-empty. |
| name | string | yes | Site name. Non-empty. |
| clientId | string | yes | Client identifier. |

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "code": "string",
    "name": "string",
    "clientId": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR, NOT_FOUND (client), CONFLICT (duplicate code).

**Side Effects:** Site created. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Code and name are non-empty. Client exists.

---

#### Update Site

**HTTP Method:** PATCH
**URL Pattern:** /api/v1/ledger/sites/{siteId}
**Required Role:** ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| siteId | string | Site identifier. |

**Request Body Schema:**

```json
{
  "code": "string",
  "name": "string",
  "isActive": true
}
```

All fields optional.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "code": "string",
    "name": "string",
    "clientId": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, VALIDATION_ERROR, CONFLICT (duplicate code).

**Side Effects:** Site updated. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Site exists.

---

#### List Vendors

**HTTP Method:** GET
**URL Pattern:** /api/v1/ledger/vendors
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| vendorTypeId | string | no | Filter by vendor type identifier. |
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "vendorTypeId": "string",
      "vendorTypeName": "string",
      "isActive": true
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Create Vendor

**HTTP Method:** POST
**URL Pattern:** /api/v1/ledger/vendors
**Required Role:** ADMIN
**Required Current State:** N/A

**Request Body Schema:**

```json
{
  "name": "string",
  "vendorTypeId": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Unique vendor name within type. Non-empty. |
| vendorTypeId | string | yes | Vendor type identifier. |

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "name": "string",
    "vendorTypeId": "string",
    "vendorTypeName": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR, NOT_FOUND (vendor type), CONFLICT (duplicate name within type).

**Side Effects:** Vendor created. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Name is non-empty. Vendor type exists.

---

#### Update Vendor

**HTTP Method:** PATCH
**URL Pattern:** /api/v1/ledger/vendors/{vendorId}
**Required Role:** ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| vendorId | string | Vendor identifier. |

**Request Body Schema:**

```json
{
  "name": "string",
  "isActive": true
}
```

All fields optional.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "name": "string",
    "vendorTypeId": "string",
    "vendorTypeName": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, VALIDATION_ERROR, CONFLICT (duplicate name within type).

**Side Effects:** Vendor updated. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Vendor exists.

---

#### List Subcontractors

**HTTP Method:** GET
**URL Pattern:** /api/v1/ledger/subcontractors
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| scopeId | string | no | Filter by scope identifier. |
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "scopeId": "string",
      "scopeName": "string",
      "isActive": true
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Create Subcontractor

**HTTP Method:** POST
**URL Pattern:** /api/v1/ledger/subcontractors
**Required Role:** ADMIN
**Required Current State:** N/A

**Request Body Schema:**

```json
{
  "name": "string",
  "scopeId": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Unique subcontractor name within scope. Non-empty. |
| scopeId | string | yes | Subcontractor scope identifier. |

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "name": "string",
    "scopeId": "string",
    "scopeName": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR, NOT_FOUND (scope), CONFLICT (duplicate name within scope).

**Side Effects:** Subcontractor created. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Name is non-empty. Scope exists.

---

#### Update Subcontractor

**HTTP Method:** PATCH
**URL Pattern:** /api/v1/ledger/subcontractors/{subcontractorId}
**Required Role:** ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| subcontractorId | string | Subcontractor identifier. |

**Request Body Schema:**

```json
{
  "name": "string",
  "isActive": true
}
```

All fields optional.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "name": "string",
    "scopeId": "string",
    "scopeName": "string",
    "isActive": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, VALIDATION_ERROR, CONFLICT (duplicate name within scope).

**Side Effects:** Subcontractor updated. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** None.

**Preconditions:** Actor has role ADMIN. Subcontractor exists.

---

#### List Vendor Types

**HTTP Method:** GET
**URL Pattern:** /api/v1/ledger/vendor-types
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "name": "string"
    }
  ]
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### List Subcontractor Scopes

**HTTP Method:** GET
**URL Pattern:** /api/v1/ledger/scopes
**Required Role:** Any authenticated user
**Required Current State:** N/A

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "name": "string"
    }
  ]
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

### PaymentBatch

#### Create Batch

**HTTP Method:** POST
**URL Pattern:** /api/v1/batches
**Required Role:** CREATOR
**Required Current State:** N/A (creates new entity)

**Request Body Schema:**

```json
{
  "title": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | yes | Non-empty batch title. |

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "title": "string",
    "status": "DRAFT",
    "createdAt": "2026-03-01T14:30:00Z",
    "createdBy": "string",
    "submittedAt": null,
    "completedAt": null,
    "requestCount": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR (empty title).

**Side Effects:** PaymentBatch created with status DRAFT. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required. Duplicate key returns original created batch.

**Concurrency Handling Requirements:** None (new entity).

**Preconditions:** Actor has role CREATOR. Title is non-empty.

---

#### Get Batch

**HTTP Method:** GET
**URL Pattern:** /api/v1/batches/{batchId}
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "title": "string",
    "status": "DRAFT",
    "createdAt": "2026-03-01T14:30:00Z",
    "createdBy": "string",
    "submittedAt": null,
    "completedAt": null,
    "requests": [
      {
        "id": "string",
        "amount": "1000.00",
        "currency": "USD",
        "beneficiaryName": "string",
        "beneficiaryAccount": "string",
        "purpose": "string",
        "entityType": null,
        "vendorId": null,
        "subcontractorId": null,
        "siteId": null,
        "baseAmount": null,
        "extraAmount": null,
        "totalAmount": null,
        "entityName": null,
        "siteCode": null,
        "status": "DRAFT",
        "createdAt": "2026-03-01T14:30:00Z",
        "createdBy": "string"
      }
    ]
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### List Batches

**HTTP Method:** GET
**URL Pattern:** /api/v1/batches
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | no | Filter by batch status. One of DRAFT, SUBMITTED, PROCESSING, COMPLETED, CANCELLED. |
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "status": "DRAFT",
      "createdAt": "2026-03-01T14:30:00Z",
      "createdBy": "string",
      "submittedAt": null,
      "completedAt": null,
      "requestCount": 0
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR (invalid status).

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Submit Batch

**HTTP Method:** POST
**URL Pattern:** /api/v1/batches/{batchId}/submit
**Required Role:** CREATOR
**Required Current State:** PaymentBatch DRAFT; all PaymentRequests in batch DRAFT

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |

**Request Body Schema:** Empty body or `{}`.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "title": "string",
    "status": "SUBMITTED",
    "createdAt": "2026-03-01T14:30:00Z",
    "createdBy": "string",
    "submittedAt": "2026-03-01T15:00:00Z",
    "completedAt": null,
    "requests": [
      {
        "id": "string",
        "status": "PENDING_APPROVAL"
      }
    ]
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (batch not DRAFT or requests not all DRAFT), PRECONDITION_FAILED (empty batch).

**Side Effects:** PaymentBatch transitions to SUBMITTED then PROCESSING. All PaymentRequests transition DRAFT to SUBMITTED then PENDING_APPROVAL. AuditLog entries created for batch and each request.

**Idempotency Rules:** If batch is already SUBMITTED or PROCESSING, return success with current batch state. No duplicate transitions. No duplicate AuditLog entries.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentBatch. Exclusive row-level locks on all PaymentRequests in batch. Lock until commit.

**Preconditions:** PaymentBatch exists. PaymentBatch status is DRAFT. Batch contains at least one PaymentRequest. All PaymentRequests are in DRAFT. Actor has role CREATOR. Actor is the batch creator.

---

#### Cancel Batch

**HTTP Method:** POST
**URL Pattern:** /api/v1/batches/{batchId}/cancel
**Required Role:** CREATOR
**Required Current State:** PaymentBatch DRAFT

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |

**Request Body Schema:** Empty body or `{}`.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "title": "string",
    "status": "CANCELLED",
    "createdAt": "2026-03-01T14:30:00Z",
    "createdBy": "string",
    "submittedAt": null,
    "completedAt": "2026-03-01T15:00:00Z"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (batch not DRAFT).

**Side Effects:** PaymentBatch transitions to CANCELLED. CompletedAt set. AuditLog entry created.

**Idempotency Rules:** If batch is already CANCELLED, return success with current batch state.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentBatch. Lock until commit.

**Preconditions:** PaymentBatch exists. PaymentBatch status is DRAFT. Actor has role CREATOR. Actor is the batch creator.

---

### PaymentRequest

#### PaymentRequest Response Schema

All PaymentRequest detail endpoints return the following schema. Legacy fields and Phase 2 ledger fields coexist. A request uses either the legacy fields (amount, beneficiaryName, and similar) or the ledger-driven fields (entityType, vendorId, and similar), never both simultaneously.

```json
{
  "id": "string",
  "batchId": "string",
  "status": "DRAFT",
  "currency": "USD",
  "createdAt": "2026-03-01T14:30:00Z",
  "createdBy": "string",
  "updatedAt": "2026-03-01T14:35:00Z",
  "updatedBy": "string",

  "amount": "1000.00",
  "beneficiaryName": "string",
  "beneficiaryAccount": "string",
  "purpose": "string",

  "entityType": "VENDOR",
  "vendorId": "string",
  "subcontractorId": null,
  "siteId": "string",
  "baseAmount": "900.00",
  "extraAmount": "100.00",
  "totalAmount": "1000.00",
  "entityName": "string",
  "siteCode": "string",

  "approval": null
}
```

**Field Reference:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | PaymentRequest identifier. |
| batchId | UUID | Parent PaymentBatch identifier. |
| status | string | One of DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED, PAID. |
| currency | string | Three-letter ISO 4217 code. |
| createdAt | datetime | ISO 8601. |
| createdBy | UUID | User identifier. |
| updatedAt | datetime | ISO 8601. Null if never updated. |
| updatedBy | UUID | User identifier. Null if never updated. |
| amount | decimal | Legacy field. Null for ledger-driven requests. |
| beneficiaryName | string | Legacy field. Null for ledger-driven requests. |
| beneficiaryAccount | string | Legacy field. Null for ledger-driven requests. |
| purpose | string | Legacy field. Null for ledger-driven requests. |
| entityType | string | VENDOR or SUBCONTRACTOR. Null for legacy requests. |
| vendorId | UUID | Null if entityType is not VENDOR. |
| subcontractorId | UUID | Null if entityType is not SUBCONTRACTOR. |
| siteId | UUID | Null for legacy requests. |
| baseAmount | decimal | Base payment amount. Null for legacy requests. |
| extraAmount | decimal | Additional amount. Null if no extra. |
| totalAmount | decimal | baseAmount + extraAmount. Null for legacy requests. |
| entityName | string | Snapshot of vendor or subcontractor name at time of creation. |
| siteCode | string | Snapshot of site code at time of creation. |
| approval | object | Null if no ApprovalRecord. See approval schema below. |

**Approval sub-object:**

```json
{
  "decision": "APPROVED",
  "comment": "string",
  "approverId": "string",
  "createdAt": "2026-03-01T15:00:00Z"
}
```

---

#### Add Payment Request

**HTTP Method:** POST
**URL Pattern:** /api/v1/batches/{batchId}/requests
**Required Role:** CREATOR
**Required Current State:** PaymentBatch DRAFT

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |

**Request Body Schema (Legacy):**

```json
{
  "amount": "1000.00",
  "currency": "USD",
  "beneficiaryName": "string",
  "beneficiaryAccount": "string",
  "purpose": "string"
}
```

**Request Body Schema (Ledger-driven):**

```json
{
  "entityType": "VENDOR",
  "vendorId": "string",
  "siteId": "string",
  "baseAmount": "900.00",
  "extraAmount": "100.00",
  "extraReason": "string",
  "currency": "USD"
}
```

Legacy and ledger-driven fields are mutually exclusive. Do not mix them in a single request.

**Success Response Schema:** See PaymentRequest Response Schema above.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND (batch or ledger entity), INVALID_STATE (batch not DRAFT), VALIDATION_ERROR.

**Side Effects:** PaymentRequest created with status DRAFT. AuditLog entry created. Snapshots populated from ledger entities for ledger-driven requests.

**Idempotency Rules:** Idempotency-Key required. Duplicate key returns original created request.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentBatch. Lock until commit.

**Preconditions:** PaymentBatch exists in DRAFT. Actor has role CREATOR and is the batch creator.

---

#### Update Payment Request

**HTTP Method:** PATCH
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}
**Required Role:** CREATOR
**Required Current State:** PaymentRequest DRAFT

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:**

All fields optional. Provided fields are updated. Omitted fields are unchanged.

```json
{
  "amount": "1000.00",
  "currency": "USD",
  "beneficiaryName": "string",
  "beneficiaryAccount": "string",
  "purpose": "string"
}
```

**Success Response Schema:** See PaymentRequest Response Schema above.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not DRAFT), VALIDATION_ERROR.

**Side Effects:** PaymentRequest fields updated. UpdatedAt and UpdatedBy set. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit.

**Preconditions:** PaymentRequest exists in DRAFT. Belongs to specified batch. Actor has role CREATOR and is the batch creator.

---

#### Get Payment Request (nested)

**HTTP Method:** GET
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": { ... }
}
```

See PaymentRequest Response Schema. Also includes:

```json
{
  "soaVersions": [
    {
      "id": "string",
      "versionNumber": 1,
      "uploadedAt": "2026-03-01T14:32:00Z",
      "uploadedBy": "string"
    }
  ]
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Get Payment Request (standalone)

**HTTP Method:** GET
**URL Pattern:** /api/v1/requests/{requestId}
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:** None.

**Success Response Schema:** Same as Get Payment Request (nested) above.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### List Pending Requests

**HTTP Method:** GET
**URL Pattern:** /api/v1/requests
**Required Role:** APPROVER or ADMIN
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | no | Filter by request status. Default PENDING_APPROVAL. One of DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED, PAID. |
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "batchId": "string",
      "batchTitle": "string",
      "amount": "1000.00",
      "currency": "USD",
      "beneficiaryName": "string",
      "entityName": "string",
      "entityType": "VENDOR",
      "purpose": "string",
      "status": "PENDING_APPROVAL",
      "createdAt": "2026-03-01T14:30:00Z"
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR (invalid status).

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

### Approval

#### Approve Request

**HTTP Method:** POST
**URL Pattern:** /api/v1/requests/{requestId}/approve
**Required Role:** APPROVER
**Required Current State:** PaymentRequest PENDING_APPROVAL

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:**

```json
{
  "comment": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| comment | string | no | Optional comment from approver. |

**Success Response Schema:**

```json
{
  "data": { ... }
}
```

See PaymentRequest Response Schema. Status will be APPROVED.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not PENDING_APPROVAL), CONFLICT (already approved).

**Side Effects:** ApprovalRecord created with decision APPROVED. PaymentRequest transitions to APPROVED. UpdatedAt and UpdatedBy set. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required. If ApprovalRecord already exists for this request, return success with current state. No duplicate ApprovalRecord. No duplicate AuditLog.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit. If ApprovalRecord already exists, do not create another.

**Preconditions:** PaymentRequest exists in PENDING_APPROVAL. No ApprovalRecord exists. Actor has role APPROVER.

---

#### Reject Request

**HTTP Method:** POST
**URL Pattern:** /api/v1/requests/{requestId}/reject
**Required Role:** APPROVER
**Required Current State:** PaymentRequest PENDING_APPROVAL

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:**

```json
{
  "comment": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| comment | string | no | Optional comment from approver. |

**Success Response Schema:**

```json
{
  "data": { ... }
}
```

See PaymentRequest Response Schema. Status will be REJECTED.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not PENDING_APPROVAL), CONFLICT (already rejected).

**Side Effects:** ApprovalRecord created with decision REJECTED. PaymentRequest transitions to REJECTED. UpdatedAt and UpdatedBy set. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required. If ApprovalRecord already exists, return success with current state. No duplicate ApprovalRecord. No duplicate AuditLog.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit.

**Preconditions:** PaymentRequest exists in PENDING_APPROVAL. No ApprovalRecord exists. Actor has role APPROVER.

---

#### Mark Request Paid

**HTTP Method:** POST
**URL Pattern:** /api/v1/requests/{requestId}/mark-paid
**Required Role:** ADMIN
**Required Current State:** PaymentRequest APPROVED

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:** Empty body or `{}`.

**Success Response Schema:**

```json
{
  "data": { ... }
}
```

See PaymentRequest Response Schema. Status will be PAID.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not APPROVED).

**Side Effects:** PaymentRequest transitions to PAID. UpdatedAt and UpdatedBy set. AuditLog entry created. If all requests in batch are PAID, batch transitions to COMPLETED.

**Idempotency Rules:** Idempotency-Key required. If request is already PAID, return success with current state.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit.

**Preconditions:** PaymentRequest exists in APPROVED. Actor has role ADMIN.

---

### SOA

#### Upload SOA

**HTTP Method:** POST
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}/soa
**Required Role:** CREATOR
**Required Current State:** PaymentRequest DRAFT

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:** multipart/form-data. Field name: `file`. Document binary.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "requestId": "string",
    "versionNumber": 1,
    "documentReference": "string",
    "source": "UPLOAD",
    "uploadedAt": "2026-03-01T14:32:00Z",
    "uploadedBy": "string"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not DRAFT), VALIDATION_ERROR (missing file).

**Side Effects:** SOAVersion created. VersionNumber assigned (1 if first, else max+1). Document stored. AuditLog entry created.

**Idempotency Rules:** Idempotency-Key required. Each upload creates a new SOAVersion.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. VersionNumber computed within locked section.

**Preconditions:** PaymentRequest exists in DRAFT. Belongs to specified batch. Actor has role CREATOR and is the batch creator.

---

#### List SOA Versions

**HTTP Method:** GET
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}/soa
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "requestId": "string",
      "versionNumber": 1,
      "source": "UPLOAD",
      "uploadedAt": "2026-03-01T14:32:00Z",
      "uploadedBy": "string"
    }
  ]
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Get SOA Document

**HTTP Method:** GET
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}/soa/{versionId}
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |
| requestId | string | PaymentRequest identifier. |
| versionId | string | SOAVersion identifier. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "requestId": "string",
    "versionNumber": 1,
    "source": "UPLOAD",
    "uploadedAt": "2026-03-01T14:32:00Z",
    "uploadedBy": "string",
    "downloadUrl": "string"
  }
}
```

The `downloadUrl` points to the download endpoint below. The client performs a separate GET to retrieve the binary.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Download SOA Document

**HTTP Method:** GET
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}/soa/{versionId}/download
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |
| requestId | string | PaymentRequest identifier. |
| versionId | string | SOAVersion identifier. |

**Request Body Schema:** None.

**Success Response:** File binary (FileResponse). Content-Disposition: attachment. Not a JSON response.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND (404 if file not found on storage).

**Side Effects:** AuditLog entry created with event type SOA_DOWNLOADED.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### Export Batch SOA

**HTTP Method:** GET
**URL Pattern:** /api/v1/batches/{batchId}/soa-export
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| export | string | yes | Output format. One of `pdf` or `excel`. Note: parameter name is `export`, not `format`, to avoid conflict with DRF content negotiation. |

**Request Body Schema:** None.

**Success Response:** File binary. PDF or Excel file depending on `export` parameter. Not a JSON response.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND (batch), VALIDATION_ERROR (missing or invalid export parameter).

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

### Audit Logs

#### Query Audit Log

**HTTP Method:** GET
**URL Pattern:** /api/v1/audit
**Required Role:** CREATOR, APPROVER, VIEWER, or ADMIN
**Required Current State:** N/A

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| entityType | string | no | Filter by entity type. One of PaymentBatch, PaymentRequest, Client, Site, Vendor, Subcontractor, SOAVersion. |
| entityId | string | no | Filter by entity identifier. |
| actorId | string | no | Filter by actor (user) identifier. |
| fromDate | string | no | ISO 8601 date. Entries on or after this date. |
| toDate | string | no | ISO 8601 date. Entries on or before this date. |
| limit | integer | no | Max results. Default 50, max 100. |
| offset | integer | no | Pagination offset. Default 0. |

**Request Body Schema:** None.

**Success Response Schema:**

```json
{
  "data": [
    {
      "id": "string",
      "eventType": "BATCH_SUBMITTED",
      "actorId": "string",
      "entityType": "PaymentBatch",
      "entityId": "string",
      "previousState": null,
      "newState": "{\"status\":\"SUBMITTED\"}",
      "occurredAt": "2026-03-01T15:00:00Z"
    }
  ],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR (invalid entityType, fromDate, toDate).

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

## API Versioning Policy

This document specifies v1 of the API. The base path `/api/v1/` is stable and backward-compatible.

### v1 Stability Guarantees

1. No response fields will be renamed in v1.
2. No response fields will be removed in v1.
3. No permissions will be broadened in v1 (a role that cannot access an endpoint today cannot access it in a future v1 release).
4. No URL patterns will change in v1.
5. No request field types will change in v1.

### Breaking Change Policy

Any of the following require a new API version (`/api/v2/`):

- Renaming or removing a response field
- Changing a field type
- Removing an endpoint
- Changing required permissions
- Changing URL structure

New optional response fields may be added to v1 without a version bump.

---

## API Freeze Declaration

This API contract specification is frozen for Internal Payments v1. No endpoint, HTTP method, URL pattern, request schema, response schema, error code, precondition, or concurrency requirement may be added, removed, or altered without a formal change control process and document revision.

**Freeze Date:** 2026-03-01
**Freeze Version:** v2.0
**Previous Version:** v1.0 (2025-02-11)

### Changes from v1.0 to v2.0

1. Added ADMIN role to all role tables and permission definitions.
2. Corrected `mark-paid` permission from CREATOR/APPROVER to ADMIN-only.
3. Added `POST /api/v1/users` endpoint (ADMIN-only user creation).
4. Added Phase 2 ledger fields to PaymentRequest response schema: entityType, vendorId, subcontractorId, siteId, baseAmount, extraAmount, totalAmount, entityName, siteCode.
5. Added full Reference Data section documenting all 10 ledger endpoints.
6. Added `GET .../soa/{versionId}/download` endpoint (file binary download).
7. Added `GET /api/v1/batches/{batchId}/soa-export` endpoint (batch export).
8. Added API Versioning Policy section.
9. Clarified Idempotency-Key requirement for all mutation endpoints.
10. Updated audit log entityType filter to include ledger entity types.
