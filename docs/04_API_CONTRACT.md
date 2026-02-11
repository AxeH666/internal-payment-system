# API Contract Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | API Contract Specification |
| Project | Internal Payment Workflow System |
| Version | 1.0 |
| Scope | MVP v1 |
| Base Path | /api/v1 |

---

## General API Principles

1. All endpoints use JSON for request and response bodies. Content-Type is application/json.

2. All dates and timestamps use ISO 8601 format (e.g. 2025-02-11T14:30:00Z).

3. All identifiers are opaque strings. The implementation defines the format.

4. All mutations are task-based. No generic create, update, or delete endpoints. Mutations correspond to domain actions (submit, approve, reject, mark-paid).

5. No endpoint may trigger an illegal state transition. Preconditions are enforced before any state change.

6. Pagination uses limit and offset query parameters. Default limit is 50. Maximum limit is 100.

---

## Authentication Requirements

1. All endpoints except Authentication group require a valid session or bearer token.

2. The authentication mechanism is implementation-defined. The contract assumes the following: the server returns 401 Unauthorized when no valid credentials are presented; the server returns 403 Forbidden when credentials are valid but the user lacks the required role.

3. The authenticated user identity and role are available to the server for authorization checks.

4. Session or token lifetime is implementation-defined.

---

## Standard Response Format

### Success Response (Single Resource)

```json
{
  "data": { ... }
}
```

The `data` field contains the resource object.

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

The `data` field is an array of resource objects. The `meta` field contains pagination metadata.

### Success Response (Mutation)

```json
{
  "data": { ... }
}
```

The `data` field contains the updated resource or the created resource.

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

The `details` field is optional and may contain additional context (e.g. field names, constraint violated).

### Standard Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid authentication. |
| FORBIDDEN | 403 | Authenticated user lacks required role. |
| NOT_FOUND | 404 | Requested resource does not exist. |
| VALIDATION_ERROR | 400 | Request body or parameters fail validation. |
| INVALID_STATE | 409 | Entity is not in the required state for the operation. |
| PRECONDITION_FAILED | 412 | One or more preconditions are not satisfied. |
| CONFLICT | 409 | Concurrent modification or duplicate operation. |
| INTERNAL_ERROR | 500 | Unrecoverable server error. |

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
| token | Session or bearer token for subsequent requests. |
| user.id | User identifier. |
| user.username | User login identifier. |
| user.displayName | Human-readable name. |
| user.role | One of CREATOR, APPROVER, VIEWER. |

**Possible Error Codes:** UNAUTHORIZED (invalid credentials), VALIDATION_ERROR (missing username or password).

**Side Effects:** Session created or token issued. Implementation-defined.

**Idempotency Rules:** N/A (read-like for authentication; repeated calls with same credentials produce new tokens or extend session).

**Concurrency Handling Requirements:** None.

---

#### Logout

**HTTP Method:** POST  
**URL Pattern:** /api/v1/auth/logout  
**Required Role:** Any authenticated user  
**Required Current State:** N/A  

**Request Body Schema:** Empty body or `{}`.

**Success Response Schema:**

```json
{
  "data": {
    "success": true
  }
}
```

**Possible Error Codes:** UNAUTHORIZED.

**Side Effects:** Session invalidated or token revoked.

**Idempotency Rules:** Multiple logout calls return success. No side effects after first logout.

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
**Required Role:** CREATOR, APPROVER, or VIEWER  
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
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "submittedAt": null,
    "completedAt": null,
    "requestCount": 0
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR (empty title).

**Side Effects:** PaymentBatch created with status DRAFT. AuditLog entry created.

**Idempotency Rules:** Not idempotent. Each call creates a new batch. Client may send Idempotency-Key header; implementation may return 409 CONFLICT if key is reused.

**Concurrency Handling Requirements:** None (new entity).

**Preconditions:** Actor has role CREATOR. Title is non-empty.

---

#### Get Batch

**HTTP Method:** GET  
**URL Pattern:** /api/v1/batches/{batchId}  
**Required Role:** CREATOR, APPROVER, or VIEWER  
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
    "createdAt": "2025-02-11T14:30:00Z",
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
        "status": "DRAFT",
        "createdAt": "2025-02-11T14:30:00Z",
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
**Required Role:** CREATOR, APPROVER, or VIEWER  
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
      "createdAt": "2025-02-11T14:30:00Z",
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
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "submittedAt": "2025-02-11T15:00:00Z",
    "completedAt": null,
    "requests": [
      {
        "id": "string",
        "status": "SUBMITTED"
      }
    ]
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (batch not DRAFT or requests not all DRAFT), PRECONDITION_FAILED (empty batch, invalid request data).

**Side Effects:** PaymentBatch transitions to SUBMITTED. Submitted At set. All PaymentRequests in batch transition DRAFT to SUBMITTED. Batch transitions to PROCESSING. All PaymentRequests transition SUBMITTED to PENDING_APPROVAL. AuditLog entries created for batch and each request.

**Idempotency Rules:** If batch is already SUBMITTED, return success with current batch state. No duplicate transitions. No duplicate AuditLog entries.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentBatch. Exclusive row-level locks on all PaymentRequests in batch. Locks held in consistent order (batch first, then requests by identifier). Lock until commit.

**Preconditions:** PaymentBatch exists. PaymentBatch status is DRAFT. Batch has non-empty title. Batch contains at least one PaymentRequest. All PaymentRequests in batch are in DRAFT. All PaymentRequests have valid amount, currency, beneficiary name, beneficiary account, purpose. Actor has role CREATOR. Actor is the batch creator.

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
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "submittedAt": null,
    "completedAt": "2025-02-11T15:00:00Z"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (batch not DRAFT).

**Side Effects:** PaymentBatch transitions to CANCELLED. Completed At set. AuditLog entry created.

**Idempotency Rules:** If batch is already CANCELLED, return success with current batch state. No duplicate transitions.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentBatch. Lock until commit.

**Preconditions:** PaymentBatch exists. PaymentBatch status is DRAFT. Actor has role CREATOR. Actor is the batch creator.

---

### PaymentRequest

#### Add Payment Request

**HTTP Method:** POST  
**URL Pattern:** /api/v1/batches/{batchId}/requests  
**Required Role:** CREATOR  
**Required Current State:** PaymentBatch DRAFT  

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| batchId | string | PaymentBatch identifier. |

**Request Body Schema:**

```json
{
  "amount": "1000.00",
  "currency": "USD",
  "beneficiaryName": "string",
  "beneficiaryAccount": "string",
  "purpose": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | string | yes | Positive decimal. |
| currency | string | yes | Three-letter ISO 4217 code. |
| beneficiaryName | string | yes | Non-empty recipient name. |
| beneficiaryAccount | string | yes | Non-empty account identifier. |
| purpose | string | yes | Non-empty payment purpose. |

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "batchId": "string",
    "amount": "1000.00",
    "currency": "USD",
    "beneficiaryName": "string",
    "beneficiaryAccount": "string",
    "purpose": "string",
    "status": "DRAFT",
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND (batch), INVALID_STATE (batch not DRAFT), VALIDATION_ERROR (invalid amount, currency, or empty required fields).

**Side Effects:** PaymentRequest created with status DRAFT. AuditLog entry created.

**Idempotency Rules:** Not idempotent. Each call creates a new request.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentBatch. Lock until commit.

**Preconditions:** PaymentBatch exists. PaymentBatch status is DRAFT. Actor has role CREATOR. Actor is the batch creator. Amount is positive. Currency is valid. BeneficiaryName and BeneficiaryAccount are non-empty. Purpose is non-empty.

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

```json
{
  "amount": "1000.00",
  "currency": "USD",
  "beneficiaryName": "string",
  "beneficiaryAccount": "string",
  "purpose": "string"
}
```

All fields optional. Provided fields are updated. Omitted fields are unchanged.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "batchId": "string",
    "amount": "1000.00",
    "currency": "USD",
    "beneficiaryName": "string",
    "beneficiaryAccount": "string",
    "purpose": "string",
    "status": "DRAFT",
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "updatedAt": "2025-02-11T14:35:00Z",
    "updatedBy": "string"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not DRAFT), VALIDATION_ERROR (invalid amount, currency, or empty required fields).

**Side Effects:** PaymentRequest amount, currency, beneficiaryName, beneficiaryAccount, purpose updated. Updated At and Updated By set. AuditLog entry created.

**Idempotency Rules:** If called twice with identical payload and request is already in DRAFT with same values, return success. No duplicate AuditLog for no-op.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit.

**Preconditions:** PaymentRequest exists. PaymentRequest status is DRAFT. PaymentRequest belongs to specified batch. Actor has role CREATOR. Actor is the batch creator. If amount provided, must be positive. If currency provided, must be valid. If beneficiaryName or beneficiaryAccount provided, must be non-empty. If purpose provided, must be non-empty.

---

#### Get Payment Request

**HTTP Method:** GET  
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}  
**Required Role:** CREATOR, APPROVER, or VIEWER  
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
  "data": {
    "id": "string",
    "batchId": "string",
    "amount": "1000.00",
    "currency": "USD",
    "beneficiaryName": "string",
    "beneficiaryAccount": "string",
    "purpose": "string",
    "status": "DRAFT",
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "updatedAt": "2025-02-11T14:35:00Z",
    "updatedBy": "string",
    "approval": null,
    "soaVersions": [
      {
        "id": "string",
        "versionNumber": 1,
        "uploadedAt": "2025-02-11T14:32:00Z",
        "uploadedBy": "string"
      }
    ]
  }
}
```

The `approval` field is null when no ApprovalRecord exists. When an ApprovalRecord exists, it contains:

```json
{
  "decision": "APPROVED",
  "comment": "string",
  "approverId": "string",
  "createdAt": "2025-02-11T15:00:00Z"
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

#### List Pending Requests

**HTTP Method:** GET  
**URL Pattern:** /api/v1/requests  
**Required Role:** APPROVER  
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
      "purpose": "string",
      "status": "PENDING_APPROVAL",
      "createdAt": "2025-02-11T14:30:00Z"
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
  "data": {
    "id": "string",
    "batchId": "string",
    "amount": "1000.00",
    "currency": "USD",
    "beneficiaryName": "string",
    "beneficiaryAccount": "string",
    "purpose": "string",
    "status": "APPROVED",
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "updatedAt": "2025-02-11T15:00:00Z",
    "updatedBy": "string",
    "approval": {
      "decision": "APPROVED",
      "comment": "string",
      "approverId": "string",
      "createdAt": "2025-02-11T15:00:00Z"
    }
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not PENDING_APPROVAL).

**Side Effects:** ApprovalRecord created with Decision APPROVED. PaymentRequest transitions to APPROVED. Updated At and Updated By set. AuditLog entry created.

**Idempotency Rules:** If ApprovalRecord already exists for this request (regardless of decision), return success with current request state. No duplicate ApprovalRecord. No duplicate AuditLog.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit. If ApprovalRecord already exists for this request, do not create another.

**Preconditions:** PaymentRequest exists. PaymentRequest status is PENDING_APPROVAL. No ApprovalRecord exists for this request. Actor has role APPROVER.

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
  "data": {
    "id": "string",
    "batchId": "string",
    "amount": "1000.00",
    "currency": "USD",
    "beneficiaryName": "string",
    "beneficiaryAccount": "string",
    "purpose": "string",
    "status": "REJECTED",
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "updatedAt": "2025-02-11T15:00:00Z",
    "updatedBy": "string",
    "approval": {
      "decision": "REJECTED",
      "comment": "string",
      "approverId": "string",
      "createdAt": "2025-02-11T15:00:00Z"
    }
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not PENDING_APPROVAL).

**Side Effects:** ApprovalRecord created with Decision REJECTED. PaymentRequest transitions to REJECTED. Updated At and Updated By set. AuditLog entry created.

**Idempotency Rules:** If ApprovalRecord already exists for this request (regardless of decision), return success with current request state. No duplicate ApprovalRecord. No duplicate AuditLog.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit. If ApprovalRecord already exists for this request, do not create another.

**Preconditions:** PaymentRequest exists. PaymentRequest status is PENDING_APPROVAL. No ApprovalRecord exists for this request. Actor has role APPROVER.

---

#### Mark Request Paid

**HTTP Method:** POST  
**URL Pattern:** /api/v1/requests/{requestId}/mark-paid  
**Required Role:** CREATOR or APPROVER  
**Required Current State:** PaymentRequest APPROVED  

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| requestId | string | PaymentRequest identifier. |

**Request Body Schema:** Empty body or `{}`.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "batchId": "string",
    "amount": "1000.00",
    "currency": "USD",
    "beneficiaryName": "string",
    "beneficiaryAccount": "string",
    "purpose": "string",
    "status": "PAID",
    "createdAt": "2025-02-11T14:30:00Z",
    "createdBy": "string",
    "updatedAt": "2025-02-11T15:30:00Z",
    "updatedBy": "string",
    "approval": {
      "decision": "APPROVED",
      "comment": "string",
      "approverId": "string",
      "createdAt": "2025-02-11T15:00:00Z"
    }
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not APPROVED).

**Side Effects:** PaymentRequest transitions to PAID. Updated At and Updated By set. AuditLog entry created.

**Idempotency Rules:** If request is already PAID, return success with current request state. No duplicate transition. No duplicate AuditLog.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Lock until commit.

**Preconditions:** PaymentRequest exists. PaymentRequest status is APPROVED. Actor has role CREATOR or APPROVER.

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

**Request Body Schema:** multipart/form-data with file field named `file`. Content-Type: multipart/form-data. The file is the document binary.

**Success Response Schema:**

```json
{
  "data": {
    "id": "string",
    "requestId": "string",
    "versionNumber": 1,
    "documentReference": "string",
    "uploadedAt": "2025-02-11T14:32:00Z",
    "uploadedBy": "string"
  }
}
```

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_STATE (request not DRAFT), VALIDATION_ERROR (missing file, invalid file type).

**Side Effects:** SOAVersion created. Version Number assigned (1 if first, else max+1). Document stored. AuditLog entry created.

**Idempotency Rules:** Not idempotent. Each upload creates a new SOAVersion with incremented version.

**Concurrency Handling Requirements:** Exclusive row-level lock on PaymentRequest. Version Number computed within locked section. Lock until commit.

**Preconditions:** PaymentRequest exists. PaymentRequest status is DRAFT. PaymentRequest belongs to specified batch. Actor has role CREATOR. Actor is the batch creator. File is provided and non-empty.

---

#### List SOA Versions

**HTTP Method:** GET  
**URL Pattern:** /api/v1/batches/{batchId}/requests/{requestId}/soa  
**Required Role:** CREATOR, APPROVER, or VIEWER  
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
      "uploadedAt": "2025-02-11T14:32:00Z",
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
**Required Role:** CREATOR, APPROVER, or VIEWER  
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
    "uploadedAt": "2025-02-11T14:32:00Z",
    "uploadedBy": "string",
    "downloadUrl": "string"
  }
}
```

The downloadUrl is a temporary URL. The client performs a GET request to downloadUrl to retrieve the document binary.

**Possible Error Codes:** UNAUTHORIZED, FORBIDDEN, NOT_FOUND.

**Side Effects:** None.

**Idempotency Rules:** N/A (read-only).

**Concurrency Handling Requirements:** None.

---

### Audit Logs

#### Query Audit Log

**HTTP Method:** GET  
**URL Pattern:** /api/v1/audit  
**Required Role:** CREATOR, APPROVER, or VIEWER  
**Required Current State:** N/A  

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| entityType | string | no | Filter by entity type. One of PaymentBatch, PaymentRequest. |
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
      "occurredAt": "2025-02-11T15:00:00Z"
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

## API Freeze Declaration

This API contract specification is frozen for MVP v1. No endpoint, HTTP method, URL pattern, request schema, response schema, error code, precondition, or concurrency requirement may be added, removed, or altered without a formal change control process and document revision.
