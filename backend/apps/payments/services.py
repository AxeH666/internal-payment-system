"""
Payment services - all mutations flow through this layer.

Rules:
- All mutations wrapped in transaction.atomic
- Use select_for_update for row-level locking
- Validate state transitions before changes
- Create audit entries for all mutations
- No direct model.save() from views
"""

from django.db import transaction
from django.utils import timezone
from core.exceptions import (
    ValidationError,
    InvalidStateError,
    NotFoundError,
    PermissionDeniedError,
    PreconditionFailedError,
)
from apps.payments.models import (
    PaymentBatch,
    PaymentRequest,
    ApprovalRecord,
    SOAVersion,
)
from apps.payments.state_machine import (
    validate_transition,
    is_closed_batch,
)
from apps.audit.services import create_audit_entry


def create_batch(creator_id, title):
    """
    Create a new PaymentBatch with status DRAFT.

    Args:
        creator_id: User identifier
        title: Batch title (non-empty)

    Returns:
        PaymentBatch: Created batch

    Raises:
        ValidationError: If title is empty
        NotFoundError: If creator does not exist
    """
    from apps.users.models import User

    if not title or not title.strip():
        raise ValidationError("Title must be non-empty")

    try:
        creator = User.objects.get(id=creator_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {creator_id} does not exist")

    with transaction.atomic():
        batch = PaymentBatch.objects.create(
            title=title.strip(), created_by=creator, status="DRAFT"
        )

        # Create audit entry
        create_audit_entry(
            event_type="BATCH_CREATED",
            actor_id=creator_id,
            entity_type="PaymentBatch",
            entity_id=batch.id,
            previous_state=None,
            new_state={"status": "DRAFT", "title": batch.title},
        )

        return batch


def add_request(
    batch_id,
    creator_id,
    amount,
    currency,
    beneficiary_name,
    beneficiary_account,
    purpose,
):
    """
    Add a PaymentRequest to a PaymentBatch.

    Args:
        batch_id: PaymentBatch identifier
        creator_id: User identifier (must be batch creator)
        amount: Positive decimal amount
        currency: Three-letter currency code
        beneficiary_name: Recipient name
        beneficiary_account: Account identifier
        purpose: Payment purpose

    Returns:
        PaymentRequest: Created request

    Raises:
        NotFoundError: If batch or creator does not exist
        InvalidStateError: If batch is not DRAFT
        PermissionDeniedError: If creator is not batch creator
        ValidationError: If validation fails
    """
    from apps.users.models import User

    try:
        batch = PaymentBatch.objects.select_for_update().get(id=batch_id)
    except PaymentBatch.DoesNotExist:
        raise NotFoundError(f"PaymentBatch {batch_id} does not exist")

    try:
        creator = User.objects.get(id=creator_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {creator_id} does not exist")

    # Check ownership
    if batch.created_by_id != creator_id:
        raise PermissionDeniedError("Only the batch creator can add requests")

    # Check batch state
    if batch.status != "DRAFT":
        raise InvalidStateError(
            f"Cannot add request to batch with status {batch.status}"
        )

    if is_closed_batch(batch.status):
        raise InvalidStateError("Cannot add request to closed batch")

    # Validate request data
    if not amount or amount <= 0:
        raise ValidationError("Amount must be positive")

    if not currency or len(currency) != 3:
        raise ValidationError("Currency must be a three-letter code")

    if not beneficiary_name or not beneficiary_name.strip():
        raise ValidationError("Beneficiary name must be non-empty")

    if not beneficiary_account or not beneficiary_account.strip():
        raise ValidationError("Beneficiary account must be non-empty")

    if not purpose or not purpose.strip():
        raise ValidationError("Purpose must be non-empty")

    with transaction.atomic():
        request = PaymentRequest.objects.create(
            batch=batch,
            amount=amount,
            currency=currency.upper().strip(),
            beneficiary_name=beneficiary_name.strip(),
            beneficiary_account=beneficiary_account.strip(),
            purpose=purpose.strip(),
            created_by=creator,
            status="DRAFT",
        )

        # Create audit entry
        create_audit_entry(
            event_type="REQUEST_CREATED",
            actor_id=creator_id,
            entity_type="PaymentRequest",
            entity_id=request.id,
            previous_state=None,
            new_state={
                "status": "DRAFT",
                "amount": str(request.amount),
                "currency": request.currency,
                "beneficiary_name": request.beneficiary_name,
            },
        )

        return request


def update_request(request_id, batch_id, creator_id, **fields):
    """
    Update a PaymentRequest (DRAFT only).

    Args:
        request_id: PaymentRequest identifier
        batch_id: PaymentBatch identifier (for validation)
        creator_id: User identifier (must be batch creator)
        **fields: Fields to update (amount, currency, beneficiary_name,
            beneficiary_account, purpose)

    Returns:
        PaymentRequest: Updated request

    Raises:
        NotFoundError: If request or creator does not exist
        InvalidStateError: If request is not DRAFT
        PermissionDeniedError: If creator is not batch creator
        ValidationError: If validation fails
    """
    from apps.users.models import User

    try:
        request = PaymentRequest.objects.select_for_update().get(id=request_id)
    except PaymentRequest.DoesNotExist:
        raise NotFoundError(f"PaymentRequest {request_id} does not exist")

    if str(request.batch_id) != str(batch_id):
        raise NotFoundError(
            f"PaymentRequest {request_id} does not belong to batch {batch_id}"
        )

    try:
        creator = User.objects.get(id=creator_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {creator_id} does not exist")

    # Check ownership
    if request.batch.created_by_id != creator_id:
        raise PermissionDeniedError("Only the batch creator can update requests")

    # Check request state
    if request.status != "DRAFT":
        raise InvalidStateError(f"Cannot update request with status {request.status}")

    # Check batch state
    if is_closed_batch(request.batch.status):
        raise InvalidStateError("Cannot update request in closed batch")

    # Validate and update fields
    previous_state = {
        "amount": str(request.amount),
        "currency": request.currency,
        "beneficiary_name": request.beneficiary_name,
        "beneficiary_account": request.beneficiary_account,
        "purpose": request.purpose,
    }

    if "amount" in fields:
        amount = fields["amount"]
        if not amount or amount <= 0:
            raise ValidationError("Amount must be positive")
        request.amount = amount

    if "currency" in fields:
        currency = fields["currency"]
        if not currency or len(currency) != 3:
            raise ValidationError("Currency must be a three-letter code")
        request.currency = currency.upper().strip()

    if "beneficiary_name" in fields:
        beneficiary_name = fields["beneficiary_name"]
        if not beneficiary_name or not beneficiary_name.strip():
            raise ValidationError("Beneficiary name must be non-empty")
        request.beneficiary_name = beneficiary_name.strip()

    if "beneficiary_account" in fields:
        beneficiary_account = fields["beneficiary_account"]
        if not beneficiary_account or not beneficiary_account.strip():
            raise ValidationError("Beneficiary account must be non-empty")
        request.beneficiary_account = beneficiary_account.strip()

    if "purpose" in fields:
        purpose = fields["purpose"]
        if not purpose or not purpose.strip():
            raise ValidationError("Purpose must be non-empty")
        request.purpose = purpose.strip()

    with transaction.atomic():
        request.updated_by = creator
        request.save()

        # Create audit entry
        new_state = {
            "amount": str(request.amount),
            "currency": request.currency,
            "beneficiary_name": request.beneficiary_name,
            "beneficiary_account": request.beneficiary_account,
            "purpose": request.purpose,
        }

        create_audit_entry(
            event_type="REQUEST_UPDATED",
            actor_id=creator_id,
            entity_type="PaymentRequest",
            entity_id=request.id,
            previous_state=previous_state,
            new_state=new_state,
        )

        return request


def submit_batch(batch_id, creator_id):
    """
    Submit a PaymentBatch and transition all requests to SUBMITTED -> PENDING_APPROVAL.

    Args:
        batch_id: PaymentBatch identifier
        creator_id: User identifier (must be batch creator)

    Returns:
        PaymentBatch: Updated batch

    Raises:
        NotFoundError: If batch or creator does not exist
        InvalidStateError: If batch is not DRAFT or requests not all DRAFT
        PermissionDeniedError: If creator is not batch creator
        PreconditionFailedError: If batch is empty or invalid
    """
    from apps.users.models import User

    try:
        batch = PaymentBatch.objects.select_for_update().get(id=batch_id)
    except PaymentBatch.DoesNotExist:
        raise NotFoundError(f"PaymentBatch {batch_id} does not exist")

    try:
        creator = User.objects.get(id=creator_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {creator_id} does not exist")

    # Check ownership
    if batch.created_by_id != creator_id:
        raise PermissionDeniedError("Only the batch creator can submit the batch")

    # Check batch state
    if batch.status != "DRAFT":
        # Idempotency: if already SUBMITTED, return success
        if batch.status == "SUBMITTED":
            return batch
        raise InvalidStateError(f"Cannot submit batch with status {batch.status}")

    # Get all requests with lock (consistent order by id)
    requests = list(
        PaymentRequest.objects.filter(batch=batch).select_for_update().order_by("id")
    )

    if not requests:
        raise PreconditionFailedError("Batch must contain at least one payment request")

    # Validate all requests are DRAFT
    for req in requests:
        if req.status != "DRAFT":
            raise InvalidStateError(
                f"All requests must be DRAFT. Request {req.id} has status {req.status}"
            )

        # Validate request data
        if req.amount <= 0:
            raise PreconditionFailedError(f"Request {req.id} has invalid amount")
        if not req.currency or len(req.currency) != 3:
            raise PreconditionFailedError(f"Request {req.id} has invalid currency")
        if not req.beneficiary_name or not req.beneficiary_account or not req.purpose:
            raise PreconditionFailedError(
                f"Request {req.id} has missing required fields"
            )

    with transaction.atomic():
        # Update batch
        now = timezone.now()
        batch.status = "SUBMITTED"
        batch.submitted_at = now
        batch.save()

        # Create audit entry for batch
        create_audit_entry(
            event_type="BATCH_SUBMITTED",
            actor_id=creator_id,
            entity_type="PaymentBatch",
            entity_id=batch.id,
            previous_state={"status": "DRAFT"},
            new_state={"status": "SUBMITTED", "submitted_at": now.isoformat()},
        )

        # Transition all requests: DRAFT -> SUBMITTED -> PENDING_APPROVAL
        for req in requests:
            # Transition to SUBMITTED
            validate_transition("PaymentRequest", req.status, "SUBMITTED")
            req.status = "SUBMITTED"
            req.updated_by = creator
            req.save()

            create_audit_entry(
                event_type="REQUEST_SUBMITTED",
                actor_id=creator_id,
                entity_type="PaymentRequest",
                entity_id=req.id,
                previous_state={"status": "DRAFT"},
                new_state={"status": "SUBMITTED"},
            )

            # Transition to PENDING_APPROVAL (system transition)
            validate_transition("PaymentRequest", req.status, "PENDING_APPROVAL")
            req.status = "PENDING_APPROVAL"
            req.save()

            create_audit_entry(
                event_type="REQUEST_SUBMITTED",
                actor_id=None,  # System transition
                entity_type="PaymentRequest",
                entity_id=req.id,
                previous_state={"status": "SUBMITTED"},
                new_state={"status": "PENDING_APPROVAL"},
            )

        # Transition batch to PROCESSING
        validate_transition("PaymentBatch", batch.status, "PROCESSING")
        batch.status = "PROCESSING"
        batch.save()

        create_audit_entry(
            event_type="BATCH_SUBMITTED",
            actor_id=None,  # System transition
            entity_type="PaymentBatch",
            entity_id=batch.id,
            previous_state={"status": "SUBMITTED"},
            new_state={"status": "PROCESSING"},
        )

        return batch


def cancel_batch(batch_id, creator_id):
    """
    Cancel a PaymentBatch (DRAFT only).

    Args:
        batch_id: PaymentBatch identifier
        creator_id: User identifier (must be batch creator)

    Returns:
        PaymentBatch: Updated batch

    Raises:
        NotFoundError: If batch or creator does not exist
        InvalidStateError: If batch is not DRAFT
        PermissionDeniedError: If creator is not batch creator
    """
    from apps.users.models import User

    try:
        batch = PaymentBatch.objects.select_for_update().get(id=batch_id)
    except PaymentBatch.DoesNotExist:
        raise NotFoundError(f"PaymentBatch {batch_id} does not exist")

    try:
        creator = User.objects.get(id=creator_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {creator_id} does not exist")
    # Ensure creator existence is enforced even if not otherwise referenced.
    creator.pk

    # Check ownership
    if batch.created_by_id != creator_id:
        raise PermissionDeniedError("Only the batch creator can cancel the batch")

    # Check batch state
    if batch.status != "DRAFT":
        # Idempotency: if already CANCELLED, return success
        if batch.status == "CANCELLED":
            return batch
        raise InvalidStateError(f"Cannot cancel batch with status {batch.status}")

    with transaction.atomic():
        now = timezone.now()
        batch.status = "CANCELLED"
        batch.completed_at = now
        batch.save()

        # Create audit entry
        create_audit_entry(
            event_type="BATCH_CANCELLED",
            actor_id=creator_id,
            entity_type="PaymentBatch",
            entity_id=batch.id,
            previous_state={"status": "DRAFT"},
            new_state={"status": "CANCELLED", "completed_at": now.isoformat()},
        )

        return batch


def approve_request(request_id, approver_id, comment=None):
    """
    Approve a PaymentRequest (PENDING_APPROVAL only).

    Args:
        request_id: PaymentRequest identifier
        approver_id: User identifier (must have APPROVER role)
        comment: Optional comment

    Returns:
        PaymentRequest: Updated request

    Raises:
        NotFoundError: If request or approver does not exist
        InvalidStateError: If request is not PENDING_APPROVAL
        PermissionDeniedError: If approver does not have APPROVER role
        PreconditionFailedError: If ApprovalRecord already exists
    """
    from apps.users.models import User

    try:
        request = PaymentRequest.objects.select_for_update().get(id=request_id)
    except PaymentRequest.DoesNotExist:
        raise NotFoundError(f"PaymentRequest {request_id} does not exist")

    try:
        approver = User.objects.get(id=approver_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {approver_id} does not exist")

    # Check role
    if approver.role != "APPROVER":
        raise PermissionDeniedError(
            "Only users with APPROVER role can approve requests"
        )

    # Check request state
    if request.status != "PENDING_APPROVAL":
        # Idempotency: if already APPROVED, return success
        if request.status == "APPROVED":
            return request
        raise InvalidStateError(f"Cannot approve request with status {request.status}")

    # Check if ApprovalRecord already exists
    if hasattr(request, "approval"):
        # Idempotency: return success without duplicate
        return request

    with transaction.atomic():
        # Create ApprovalRecord
        ApprovalRecord.objects.create(
            payment_request=request,
            approver=approver,
            decision="APPROVED",
            comment=comment.strip() if comment else None,
        )

        # Transition request to APPROVED
        validate_transition("PaymentRequest", request.status, "APPROVED")
        request.status = "APPROVED"
        request.updated_by = approver
        request.save()

        # Create audit entry
        create_audit_entry(
            event_type="APPROVAL_RECORDED",
            actor_id=approver_id,
            entity_type="PaymentRequest",
            entity_id=request.id,
            previous_state={"status": "PENDING_APPROVAL"},
            new_state={"status": "APPROVED", "decision": "APPROVED"},
        )

        return request


def reject_request(request_id, approver_id, comment=None):
    """
    Reject a PaymentRequest (PENDING_APPROVAL only).

    Args:
        request_id: PaymentRequest identifier
        approver_id: User identifier (must have APPROVER role)
        comment: Optional comment

    Returns:
        PaymentRequest: Updated request

    Raises:
        NotFoundError: If request or approver does not exist
        InvalidStateError: If request is not PENDING_APPROVAL
        PermissionDeniedError: If approver does not have APPROVER role
        PreconditionFailedError: If ApprovalRecord already exists
    """
    from apps.users.models import User

    try:
        request = PaymentRequest.objects.select_for_update().get(id=request_id)
    except PaymentRequest.DoesNotExist:
        raise NotFoundError(f"PaymentRequest {request_id} does not exist")

    try:
        approver = User.objects.get(id=approver_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {approver_id} does not exist")

    # Check role
    if approver.role != "APPROVER":
        raise PermissionDeniedError("Only users with APPROVER role can reject requests")

    # Check request state
    if request.status != "PENDING_APPROVAL":
        # Idempotency: if already REJECTED, return success
        if request.status == "REJECTED":
            return request
        raise InvalidStateError(f"Cannot reject request with status {request.status}")

    # Check if ApprovalRecord already exists
    if hasattr(request, "approval"):
        # Idempotency: return success without duplicate
        return request

    with transaction.atomic():
        # Create ApprovalRecord
        ApprovalRecord.objects.create(
            payment_request=request,
            approver=approver,
            decision="REJECTED",
            comment=comment.strip() if comment else None,
        )

        # Transition request to REJECTED
        validate_transition("PaymentRequest", request.status, "REJECTED")
        request.status = "REJECTED"
        request.updated_by = approver
        request.save()

        # Create audit entry
        create_audit_entry(
            event_type="APPROVAL_RECORDED",
            actor_id=approver_id,
            entity_type="PaymentRequest",
            entity_id=request.id,
            previous_state={"status": "PENDING_APPROVAL"},
            new_state={"status": "REJECTED", "decision": "REJECTED"},
        )

        return request


def mark_paid(request_id, actor_id):
    """
    Mark a PaymentRequest as PAID (APPROVED only).

    Args:
        request_id: PaymentRequest identifier
        actor_id: User identifier (must have CREATOR or APPROVER role)

    Returns:
        PaymentRequest: Updated request

    Raises:
        NotFoundError: If request or actor does not exist
        InvalidStateError: If request is not APPROVED
        PermissionDeniedError: If actor does not have required role
    """
    from apps.users.models import User

    try:
        request = PaymentRequest.objects.select_for_update().get(id=request_id)
    except PaymentRequest.DoesNotExist:
        raise NotFoundError(f"PaymentRequest {request_id} does not exist")

    try:
        actor = User.objects.get(id=actor_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {actor_id} does not exist")

    # Check role
    if actor.role not in ("CREATOR", "APPROVER"):
        raise PermissionDeniedError(
            "Only CREATOR or APPROVER can mark requests as paid"
        )

    # Check request state
    if request.status != "APPROVED":
        # Idempotency: if already PAID, return success
        if request.status == "PAID":
            return request
        raise InvalidStateError(
            f"Cannot mark paid request with status {request.status}"
        )

    with transaction.atomic():
        # Transition request to PAID
        validate_transition("PaymentRequest", request.status, "PAID")
        request.status = "PAID"
        request.updated_by = actor
        request.save()

        # Create audit entry
        create_audit_entry(
            event_type="REQUEST_PAID",
            actor_id=actor_id,
            entity_type="PaymentRequest",
            entity_id=request.id,
            previous_state={"status": "APPROVED"},
            new_state={"status": "PAID"},
        )

        # Check if batch should transition to COMPLETED
        batch = request.batch
        if batch.status == "PROCESSING":
            # Check if all requests are terminal
            all_terminal = all(
                req.status in ("APPROVED", "REJECTED", "PAID")
                for req in batch.requests.all()
            )

            if all_terminal:
                validate_transition("PaymentBatch", batch.status, "COMPLETED")
                batch.status = "COMPLETED"
                batch.completed_at = timezone.now()
                batch.save()

                create_audit_entry(
                    event_type="BATCH_COMPLETED",
                    actor_id=None,  # System transition
                    entity_type="PaymentBatch",
                    entity_id=batch.id,
                    previous_state={"status": "PROCESSING"},
                    new_state={
                        "status": "COMPLETED",
                        "completed_at": batch.completed_at.isoformat(),
                    },
                )

                # Auto-generate SOA when batch completes (original canonical flow)
                generate_soa_for_batch(batch.id)

        return request


def upload_soa(batch_id, request_id, creator_id, file):
    """
    Upload a Statement of Account document for a PaymentRequest (DRAFT only).

    Args:
        batch_id: PaymentBatch identifier
        request_id: PaymentRequest identifier
        creator_id: User identifier (must be batch creator)
        file: File object

    Returns:
        SOAVersion: Created SOA version

    Raises:
        NotFoundError: If request or creator does not exist
        InvalidStateError: If request is not DRAFT
        PermissionDeniedError: If creator is not batch creator
        ValidationError: If file is missing
    """
    from apps.users.models import User
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile

    try:
        request = PaymentRequest.objects.select_for_update().get(id=request_id)
    except PaymentRequest.DoesNotExist:
        raise NotFoundError(f"PaymentRequest {request_id} does not exist")

    if str(request.batch_id) != str(batch_id):
        raise NotFoundError(
            f"PaymentRequest {request_id} does not belong to batch {batch_id}"
        )

    try:
        creator = User.objects.get(id=creator_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {creator_id} does not exist")

    # Check ownership
    if request.batch.created_by_id != creator_id:
        raise PermissionDeniedError("Only the batch creator can upload SOA")

    # Check request state
    if request.status != "DRAFT":
        raise InvalidStateError(
            f"Cannot upload SOA for request with status {request.status}"
        )

    # Check batch state
    if is_closed_batch(request.batch.status):
        raise InvalidStateError("Cannot upload SOA for request in closed batch")

    if not file:
        raise ValidationError("File is required")

    with transaction.atomic():
        # Calculate next version number
        existing_versions = SOAVersion.objects.filter(payment_request=request).order_by(
            "-version_number"
        )
        if existing_versions.exists():
            next_version = existing_versions.first().version_number + 1
        else:
            next_version = 1

        # Store file (simplified - in production use proper storage backend)
        file_name = f"soa/{request_id}/{next_version}_{file.name}"
        file_path = default_storage.save(file_name, ContentFile(file.read()))

        # Create SOAVersion (user upload)
        soa_version = SOAVersion.objects.create(
            payment_request=request,
            version_number=next_version,
            document_reference=file_path,
            source=SOAVersion.SOURCE_UPLOAD,
            uploaded_by=creator,
        )

        # Create audit entry
        create_audit_entry(
            event_type="SOA_UPLOADED",
            actor_id=creator_id,
            entity_type="SOAVersion",
            entity_id=soa_version.id,
            previous_state=None,
            new_state={"version_number": next_version, "request_id": str(request_id)},
        )

        return soa_version


def generate_soa_for_batch(batch_id):
    """
    Auto-generate SOA when batch reaches COMPLETED.
    System creates SOA document; no manual step.
    Audit: SOA_GENERATED (actor=None for system event).

    Idempotent: skips if batch already has generated SOA.

    Args:
        batch_id: PaymentBatch identifier

    Returns:
        list[SOAVersion]: Created SOA versions (one per request), or empty if skipped
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    from apps.payments.soa_export import export_batch_soa_pdf

    try:
        batch = PaymentBatch.objects.get(id=batch_id)
    except PaymentBatch.DoesNotExist:
        return []

    # Idempotency: skip if already generated
    has_generated = SOAVersion.objects.filter(
        payment_request__batch_id=batch_id,
        source=SOAVersion.SOURCE_GENERATED,
    ).exists()
    if has_generated:
        return []

    # Generate PDF
    content, filename = export_batch_soa_pdf(batch_id)

    # Store file (single file for batch, referenced by each request)
    file_path = f"soa/generated/{batch_id}/batch_soa.pdf"
    default_storage.save(file_path, ContentFile(content))

    created = []
    with transaction.atomic():
        for request in batch.requests.all():
            # Next version for this request
            existing = SOAVersion.objects.filter(payment_request=request).order_by(
                "-version_number"
            )
            next_version = (
                existing.first().version_number + 1 if existing.exists() else 1
            )

            soa_version = SOAVersion.objects.create(
                payment_request=request,
                version_number=next_version,
                document_reference=file_path,
                source=SOAVersion.SOURCE_GENERATED,
                uploaded_by=None,  # System-generated
            )
            created.append(soa_version)

        # Audit: SOA_GENERATED (system event, no actor)
        create_audit_entry(
            event_type="SOA_GENERATED",
            actor_id=None,
            entity_type="PaymentBatch",
            entity_id=batch.id,
            previous_state=None,
            new_state={
                "batch_id": str(batch_id),
                "soa_versions_created": len(created),
            },
        )

    return created
