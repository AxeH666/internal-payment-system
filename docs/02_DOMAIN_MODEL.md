# Domain Model Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Domain Purpose

The domain models the lifecycle of internal payment requests within a single organization. It captures the creation of payment batches and requests, the approval workflow, the association of supporting documents (Statement of Account), and the immutable audit trail of all domain operations. The model excludes multi-tenancy, ledger, accounting, and external system integration.

---

## Core Entities List

1. User  
2. PaymentBatch  
3. PaymentRequest  
4. ApprovalRecord  
5. SOAVersion  
6. AuditLog  

---

## Detailed Entity Definitions

### User

**Definition:** An internal actor who can create payment requests, submit batches, approve or reject payment requests, and view audit data.

**Attributes:**
- Identifier: unique stable identity
- Username: unique human-readable login identifier
- Display Name: human-readable name for display in audit and approval records
- Role: classification determining approval authority (e.g. CREATOR, APPROVER, VIEWER)

**Ownership:** The system owns User entities. No user owns another user.

**Constraints:**
- Username must be unique within the system.
- Role must be one of the defined role classifications.

---

### PaymentBatch

**Definition:** A logical grouping of one or more payment requests submitted together for processing.

**Attributes:**
- Identifier: unique stable identity
- Title: human-readable batch label
- Status: DRAFT | SUBMITTED | PROCESSING | COMPLETED | CANCELLED
- Created At: timestamp of creation
- Created By: reference to User identifier
- Submitted At: timestamp of submission (null when status is DRAFT)
- Completed At: timestamp of completion (null when not COMPLETED or CANCELLED)

**Ownership:** The User referenced by Created By is the batch creator. The creator owns the batch until submission.

**Constraints:**
- Title must be non-empty.
- At least one PaymentRequest must exist in a submitted batch.
- Submitted At must be set when status is not DRAFT.
- Completed At must be set when status is COMPLETED or CANCELLED.

---

### PaymentRequest

**Definition:** A single payment instruction within a batch, representing a payment to be made to a beneficiary.

**Attributes:**
- Identifier: unique stable identity
- Batch Identifier: reference to PaymentBatch
- Amount: positive decimal value (currency implied by system configuration)
- Currency: three-letter currency code
- Beneficiary Name: recipient name
- Beneficiary Account: account identifier for the beneficiary
- Purpose: human-readable description of payment purpose
- Status: one of the defined PaymentRequest states
- Created At: timestamp of creation
- Created By: reference to User identifier
- Updated At: timestamp of last state change
- Updated By: reference to User identifier of last updater

**Ownership:** The User referenced by Created By owns the request until submission. After submission, ownership transfers to the approval workflow.

**Constraints:**
- Amount must be strictly positive.
- Currency must be a valid three-letter code.
- Beneficiary Name and Beneficiary Account must be non-empty.
- Purpose must be non-empty.
- A PaymentRequest belongs to exactly one PaymentBatch.
- Batch Identifier must reference an existing PaymentBatch.

---

### ApprovalRecord

**Definition:** A record of a single approval or rejection action performed on a payment request.

**Attributes:**
- Identifier: unique stable identity
- Payment Request Identifier: reference to PaymentRequest
- Approver Identifier: reference to User
- Decision: APPROVED | REJECTED
- Comment: optional text provided by the approver
- Created At: timestamp of the decision

**Ownership:** The Approver Identifier references the User who performed the action. The ApprovalRecord is owned by the PaymentRequest lifecycle.

**Constraints:**
- Payment Request Identifier must reference an existing PaymentRequest.
- Approver Identifier must reference an existing User.
- Decision must be APPROVED or REJECTED.
- One ApprovalRecord exists per approval step per PaymentRequest.

---

### SOAVersion

**Definition:** A versioned snapshot of a Statement of Account document attached to a payment request.

**Attributes:**
- Identifier: unique stable identity
- Payment Request Identifier: reference to PaymentRequest
- Version Number: positive integer, monotonically increasing per payment request
- Document Reference: storage reference or identifier for the document binary
- Uploaded At: timestamp of upload
- Uploaded By: reference to User identifier

**Ownership:** The PaymentRequest owns its SOAVersions. The User referenced by Uploaded By performed the upload.

**Constraints:**
- Payment Request Identifier must reference an existing PaymentRequest.
- Version Number must be unique per PaymentRequest.
- Document Reference must be non-empty.
- Version Number must be 1 for the first SOA of a PaymentRequest and increment by 1 for each subsequent version.

---

### AuditLog

**Definition:** An immutable chronological record of domain events.

**Attributes:**
- Identifier: unique stable identity
- Event Type: classification of the event (e.g. BATCH_CREATED, REQUEST_SUBMITTED, APPROVAL_RECORDED)
- Actor Identifier: reference to User (null for system events)
- Entity Type: type of affected entity (e.g. PaymentBatch, PaymentRequest)
- Entity Identifier: reference to affected entity
- Previous State: serialized state before change (null for creation)
- New State: serialized state after change
- Occurred At: timestamp of the event

**Ownership:** The system owns AuditLog entries. No user owns audit records.

**Constraints:**
- Event Type must be one of the defined event types.
- Entity Type and Entity Identifier must reference a valid entity.
- Occurred At must be non-null.
- Entries are append-only; no updates or deletions.

---

## State Definitions for PaymentRequest

**Enumeration of states:**

| State | Description |
|-------|-------------|
| DRAFT | Request is being created or edited. Not yet submitted. |
| SUBMITTED | Request has been submitted for approval. |
| PENDING_APPROVAL | Request is awaiting approval decision. |
| APPROVED | Request has been approved. |
| REJECTED | Request has been rejected. |
| PAID | Payment has been executed. |

**Allowed state transitions:**

| From State | To State | Condition |
|------------|----------|-----------|
| DRAFT | SUBMITTED | User submits the request. |
| DRAFT | DRAFT | User edits the request (no state change). |
| SUBMITTED | PENDING_APPROVAL | Request enters approval queue. |
| PENDING_APPROVAL | APPROVED | Approver approves. |
| PENDING_APPROVAL | REJECTED | Approver rejects. |
| APPROVED | PAID | Payment is executed. |

**Disallowed transitions:**

| From State | To State | Reason |
|------------|----------|--------|
| DRAFT | PENDING_APPROVAL | Must submit first. |
| DRAFT | APPROVED | Must submit first. |
| DRAFT | REJECTED | Must submit first. |
| DRAFT | PAID | Must submit first. |
| SUBMITTED | DRAFT | Submission is irreversible. |
| SUBMITTED | APPROVED | Must pass through PENDING_APPROVAL. |
| SUBMITTED | REJECTED | Must pass through PENDING_APPROVAL. |
| SUBMITTED | PAID | Must pass through PENDING_APPROVAL and APPROVED. |
| PENDING_APPROVAL | DRAFT | Cannot revert after submission. |
| PENDING_APPROVAL | SUBMITTED | Direction is forward only. |
| PENDING_APPROVAL | PAID | Must be approved first. |
| APPROVED | DRAFT | Cannot revert. |
| APPROVED | SUBMITTED | Cannot revert. |
| APPROVED | PENDING_APPROVAL | Cannot revert. |
| APPROVED | REJECTED | Cannot reject after approval. |
| REJECTED | Any | Rejection is terminal for that request. |
| PAID | Any | Payment is terminal. |

---

## Relationship Definitions

| Relationship | Cardinality | Description |
|--------------|-------------|-------------|
| User creates PaymentBatch | 1:N | One User may create many PaymentBatches. Each PaymentBatch has exactly one creator. |
| PaymentBatch contains PaymentRequest | 1:N | One PaymentBatch contains one or more PaymentRequests. Each PaymentRequest belongs to exactly one PaymentBatch. |
| PaymentRequest has ApprovalRecords | 1:N | One PaymentRequest may have zero or more ApprovalRecords. Each ApprovalRecord belongs to exactly one PaymentRequest. |
| User performs ApprovalRecord | 1:N | One User may perform many ApprovalRecords. Each ApprovalRecord references exactly one approver. |
| PaymentRequest has SOAVersions | 1:N | One PaymentRequest may have zero or more SOAVersions. Each SOAVersion belongs to exactly one PaymentRequest. |
| User uploads SOAVersion | 1:N | One User may upload many SOAVersions. Each SOAVersion references exactly one uploader. |
| AuditLog references User | N:1 | Many AuditLog entries may reference one User as actor. AuditLog entries may have null actor. |
| AuditLog references Entity | N:1 | Many AuditLog entries may reference one entity (PaymentBatch, PaymentRequest, ApprovalRecord, SOAVersion) by type and identifier. |

---

## Structural Invariants

1. **INV-1:** Every PaymentRequest belongs to exactly one PaymentBatch.

2. **INV-2:** The sum of PaymentRequest amounts in a PaymentBatch has no stipulated constraint; batches may contain any number of requests with any total.

3. **INV-3:** A PaymentRequest in state DRAFT may be edited; a PaymentRequest in any other state may not have its amount, currency, beneficiary, or purpose modified.

4. **INV-4:** A PaymentRequest may transition from PENDING_APPROVAL to APPROVED only if an ApprovalRecord with Decision APPROVED exists for that request.

5. **INV-5:** A PaymentRequest may transition from PENDING_APPROVAL to REJECTED only if an ApprovalRecord with Decision REJECTED exists for that request.

6. **INV-6:** A PaymentRequest in state APPROVED may transition to PAID exactly once.

7. **INV-7:** A PaymentRequest in state REJECTED or PAID may not transition to any other state.

8. **INV-8:** A PaymentBatch may be submitted only if it contains at least one PaymentRequest in state DRAFT or SUBMITTED.

9. **INV-9:** SOAVersion Version Number for a given PaymentRequest forms a strictly increasing sequence with no gaps.

10. **INV-10:** AuditLog entries are append-only; no update or delete operations apply.

11. **INV-11:** Every ApprovalRecord must reference a PaymentRequest that exists and that was in state PENDING_APPROVAL at the time of the decision.

12. **INV-12:** User Username must be unique across all User entities.

---

## Immutability Boundaries

### Immutable at Creation

The following attributes are set at entity creation and never modified:

- **User:** Identifier  
- **PaymentBatch:** Identifier, Created At, Created By  
- **PaymentRequest:** Identifier, Batch Identifier, Created At, Created By  
- **ApprovalRecord:** Identifier, Payment Request Identifier, Approver Identifier, Decision, Comment, Created At  
- **SOAVersion:** Identifier, Payment Request Identifier, Version Number, Document Reference, Uploaded At, Uploaded By  
- **AuditLog:** Identifier, Event Type, Actor Identifier, Entity Type, Entity Identifier, Previous State, New State, Occurred At  

### Immutable After State Transition

The following attributes become immutable after a specific state transition:

- **PaymentRequest Amount, Currency, Beneficiary Name, Beneficiary Account, Purpose:** Immutable after transition from DRAFT to SUBMITTED.

- **PaymentBatch Status:** Immutable after transition to COMPLETED or CANCELLED.

- **PaymentRequest Status:** Immutable after transition to REJECTED or PAID.

---

## Explicit Domain Exclusions

The following are explicitly excluded from the domain model for MVP v1:

1. **Multi-tenancy:** No tenant, organization, or company entity. Single company is assumed.

2. **Ledger:** No double-entry ledger, debits, credits, or balance tracking.

3. **Accounting engine:** No general ledger posting, chart of accounts, or accounting entries.

4. **External integrations:** No payment gateways, banks, ERP systems, or third-party APIs.

5. **Currency conversion:** No exchange rates or multi-currency conversion logic.

6. **Recurring payments:** No scheduled or recurring payment definitions.

7. **Payment method selection:** No distinction between wire, ACH, or other payment methods; payment execution is abstract.

8. **Notification or messaging:** No outbound email, SMS, or notification entities.

9. **File storage model:** Document Reference in SOAVersion is a conceptual pointer; storage mechanism is out of scope.

10. **Authentication and authorization:** User exists as a domain actor; authentication tokens, sessions, and permissions are excluded.

---

## Domain Freeze Declaration

This domain model specification is frozen for MVP v1. No entity, attribute, relationship, state, or invariant may be added, removed, or altered without a formal change control process and document revision. The exclusions listed above remain in effect until explicitly rescinded by a subsequent specification version.
