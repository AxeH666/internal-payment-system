# State Machine Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Purpose of State Machine

This document defines the state machines for PaymentRequest, PaymentBatch, and SOAVersion entities. It specifies allowed and disallowed transitions, preconditions, postconditions, role constraints, concurrency rules, and idempotency guarantees. The specification is deterministic and implementation-agnostic.

---

## PaymentRequest State Machine

### State Definitions

| State | Description |
|-------|-------------|
| DRAFT | Request is being created or edited. Not yet submitted. |
| SUBMITTED | Request has been submitted for approval. |
| PENDING_APPROVAL | Request is awaiting approval decision. |
| APPROVED | Request has been approved. |
| REJECTED | Request has been rejected. |
| PAID | Payment has been executed. |

### Allowed Transitions

| Transition | Trigger | Required Role | Required Current State | Resulting State | Side Effects |
|------------|---------|---------------|------------------------|-----------------|--------------|
| T1 | User submits request as part of batch submission | CREATOR | DRAFT | SUBMITTED | Amount, currency, beneficiary, purpose become immutable. AuditLog entry created. |
| T2 | Batch submission completes; request enters approval queue | System | SUBMITTED | PENDING_APPROVAL | AuditLog entry created. |
| T3 | Approver approves request | APPROVER | PENDING_APPROVAL | APPROVED | ApprovalRecord created with Decision APPROVED. AuditLog entry created. |
| T4 | Approver rejects request | APPROVER | PENDING_APPROVAL | REJECTED | ApprovalRecord created with Decision REJECTED. AuditLog entry created. |
| T5 | User marks payment as executed | CREATOR or APPROVER | APPROVED | PAID | AuditLog entry created. |

### Disallowed Transitions

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
| REJECTED | Any | Rejection is terminal. |
| PAID | Any | Payment is terminal. |

### Preconditions per Transition

| Transition | Preconditions |
|------------|---------------|
| T1 (DRAFT to SUBMITTED) | PaymentRequest exists. Current state is DRAFT. Amount is positive. Currency is valid. Beneficiary Name and Beneficiary Account are non-empty. Purpose is non-empty. Actor has role CREATOR. Actor is the batch creator. Batch contains at least one request. |
| T2 (SUBMITTED to PENDING_APPROVAL) | PaymentRequest exists. Current state is SUBMITTED. Batch status is SUBMITTED or PROCESSING. |
| T3 (PENDING_APPROVAL to APPROVED) | PaymentRequest exists. Current state is PENDING_APPROVAL. Actor has role APPROVER. No ApprovalRecord exists yet for this request. |
| T4 (PENDING_APPROVAL to REJECTED) | PaymentRequest exists. Current state is PENDING_APPROVAL. Actor has role APPROVER. No ApprovalRecord exists yet for this request. |
| T5 (APPROVED to PAID) | PaymentRequest exists. Current state is APPROVED. Actor has role CREATOR or APPROVER. |

### Postconditions per Transition

| Transition | Postconditions |
|------------|----------------|
| T1 | PaymentRequest status is SUBMITTED. Updated At and Updated By set. Amount, currency, beneficiary, purpose are immutable. |
| T2 | PaymentRequest status is PENDING_APPROVAL. |
| T3 | PaymentRequest status is APPROVED. ApprovalRecord exists with Decision APPROVED. |
| T4 | PaymentRequest status is REJECTED. ApprovalRecord exists with Decision REJECTED. |
| T5 | PaymentRequest status is PAID. Status is immutable. |

### Role Constraints per Transition

| Transition | Allowed Roles | Forbidden Roles |
|------------|---------------|-----------------|
| T1 | CREATOR | APPROVER, VIEWER |
| T2 | System (no user) | All user roles |
| T3 | APPROVER | CREATOR, VIEWER |
| T4 | APPROVER | CREATOR, VIEWER |
| T5 | CREATOR, APPROVER | VIEWER |

---

## PaymentBatch State Machine

### State Definitions

| State | Description |
|-------|-------------|
| DRAFT | Batch is being created or edited. Not yet submitted. |
| SUBMITTED | Batch has been submitted. Requests are in approval queue. |
| PROCESSING | Batch is being processed; approvals and rejections in progress. |
| COMPLETED | All requests in batch have reached terminal state. |
| CANCELLED | Batch was cancelled before submission. |

### Allowed Transitions

| Transition | Trigger | Required Role | Required Current State | Resulting State | Side Effects |
|------------|---------|---------------|------------------------|-----------------|--------------|
| B1 | User submits batch | CREATOR | DRAFT | SUBMITTED | Submitted At set. All PaymentRequests in batch transition DRAFT to SUBMITTED. AuditLog entry created. |
| B2 | Batch enters processing phase | System | SUBMITTED | PROCESSING | AuditLog entry created. |
| B3 | All requests in batch have reached terminal state | System | PROCESSING | COMPLETED | Completed At set. AuditLog entry created. |
| B4 | User cancels draft batch | CREATOR | DRAFT | CANCELLED | Completed At set. AuditLog entry created. |

### Disallowed Transitions

| From State | To State | Reason |
|------------|----------|--------|
| DRAFT | PROCESSING | Must submit first. |
| DRAFT | COMPLETED | Must submit first. |
| SUBMITTED | DRAFT | Submission is irreversible. |
| SUBMITTED | SUBMITTED | No self-transition. |
| SUBMITTED | COMPLETED | Must pass through PROCESSING. |
| SUBMITTED | CANCELLED | Cannot cancel after submission. |
| PROCESSING | DRAFT | Cannot revert. |
| PROCESSING | SUBMITTED | Direction is forward only. |
| PROCESSING | CANCELLED | Cannot cancel after submission. |
| COMPLETED | Any | COMPLETED is terminal. |
| CANCELLED | Any | CANCELLED is terminal. |

### Preconditions per Transition

| Transition | Preconditions |
|------------|---------------|
| B1 | PaymentBatch exists. Current state is DRAFT. Batch has non-empty title. Batch contains at least one PaymentRequest. All PaymentRequests in batch are in DRAFT. Actor has role CREATOR. Actor is the batch creator. |
| B2 | PaymentBatch exists. Current state is SUBMITTED. |
| B3 | PaymentBatch exists. Current state is PROCESSING. Every PaymentRequest in the batch has status APPROVED, REJECTED, or PAID. |
| B4 | PaymentBatch exists. Current state is DRAFT. Actor has role CREATOR. Actor is the batch creator. |

### Postconditions per Transition

| Transition | Postconditions |
|------------|----------------|
| B1 | PaymentBatch status is SUBMITTED. Submitted At is set. All contained PaymentRequests are SUBMITTED. |
| B2 | PaymentBatch status is PROCESSING. |
| B3 | PaymentBatch status is COMPLETED. Completed At is set. Status is immutable. |
| B4 | PaymentBatch status is CANCELLED. Completed At is set. Status is immutable. |

---

## SOAVersion State Behavior

### Version Increment Rules

1. The first SOAVersion for a PaymentRequest has Version Number 1.

2. Each subsequent SOAVersion for the same PaymentRequest has Version Number equal to (max existing Version Number) + 1.

3. Version Numbers form a strictly increasing sequence with no gaps.

4. Version Number is assigned at creation and is immutable.

### FINAL Version Behavior

1. When a PaymentRequest transitions from DRAFT to SUBMITTED, SOA uploads for that request are blocked.

2. The set of SOAVersions attached to the PaymentRequest at the moment of submission is the final set for that request.

3. No new SOAVersion may be created for a PaymentRequest whose status is SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED, or PAID.

### Blocking Rules

1. **Blocking rule BR-1:** SOAVersion creation is blocked when PaymentRequest status is not DRAFT.

2. **Blocking rule BR-2:** SOAVersion creation is blocked when PaymentRequest does not exist.

3. **Blocking rule BR-3:** SOAVersion creation requires the actor to have role CREATOR and to be the creator of the PaymentRequest (or have equivalent authority).

---

## Transition Invariants

1. **SMI-1:** DRAFT to PAID is forbidden. PaymentRequest must pass through SUBMITTED, PENDING_APPROVAL, and APPROVED before PAID.

2. **SMI-2:** PAID to any state is forbidden. PAID is terminal.

3. **SMI-3:** REJECTED to any state is forbidden. REJECTED is terminal.

4. **SMI-4:** COMPLETED to any state is forbidden for PaymentBatch. COMPLETED is terminal.

5. **SMI-5:** CANCELLED to any state is forbidden for PaymentBatch. CANCELLED is terminal.

6. **SMI-6:** COMPLETED and CANCELLED cannot transition to DRAFT or SUBMITTED. No CLOSED to OPEN transition.

7. **SMI-7:** Every state-changing operation must create an AuditLog entry before the transition commits.

8. **SMI-8:** ApprovalRecord creation may occur only when PaymentRequest is in PENDING_APPROVAL and only once per request.

9. **SMI-9:** SOAVersion creation is blocked when PaymentRequest is not in DRAFT (FINAL blocking).

---

## Concurrency Enforcement Requirements

1. **CER-1:** Before executing any PaymentRequest state transition, the implementation must acquire an exclusive row-level lock on the PaymentRequest entity. The lock must be held until the transition commits.

2. **CER-2:** Before executing any PaymentBatch state transition, the implementation must acquire an exclusive row-level lock on the PaymentBatch entity. The lock must be held until the transition commits.

3. **CER-3:** When executing batch submission (B1), the implementation must acquire exclusive row-level locks on the PaymentBatch and all PaymentRequests in the batch. Locks must be held in a consistent order (e.g. batch first, then requests by identifier) to prevent deadlock.

4. **CER-4:** When creating an ApprovalRecord, the implementation must hold the PaymentRequest row-level lock. The ApprovalRecord must not be created if another concurrent operation has already created an ApprovalRecord for the same PaymentRequest.

5. **CER-5:** When creating an SOAVersion, the implementation must hold the PaymentRequest row-level lock. The Version Number must be computed and assigned within the locked section.

---

## Idempotency Guarantees

1. **IG-1:** If a transition is invoked and the entity is already in the target state, the operation must return success without applying the transition again. No duplicate AuditLog entry. No duplicate ApprovalRecord.

2. **IG-2:** If a transition is invoked and the entity is in a state other than the required current state, the operation must fail with a deterministic error indicating invalid state. No partial state change.

3. **IG-3:** If a transition is invoked with the same idempotency key (when supported) and the operation has already completed, the implementation must return the result of the original operation. No duplicate side effects.

4. **IG-4:** Batch submission (B1) is idempotent with respect to the batch: if the batch is already SUBMITTED, a duplicate submission request must return success without re-submitting. PaymentRequests must not be transitioned again.

5. **IG-5:** Approval (T3) and rejection (T4) are idempotent with respect to the PaymentRequest: if an ApprovalRecord already exists for the request, a duplicate approve/reject request must return success without creating a duplicate ApprovalRecord or changing state.

---

## State Machine Freeze Declaration

This state machine specification is frozen for MVP v1. No state, transition, precondition, postcondition, role constraint, invariant, concurrency rule, or idempotency rule may be added, removed, or altered without a formal change control process and document revision.
