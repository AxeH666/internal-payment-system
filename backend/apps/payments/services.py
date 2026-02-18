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
from apps.payments.versioning import version_locked_update
from apps.audit.services import create_audit_entry
from django.db import connection


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
    from apps.users.models import User, Role

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
    amount=None,
    currency=None,
    beneficiary_name=None,
    beneficiary_account=None,
    purpose=None,
    # Phase 2: Ledger-driven fields
    entity_type=None,
    vendor_id=None,
    subcontractor_id=None,
    site_id=None,
    base_amount=None,
    extra_amount=None,
    extra_reason=None,
    idempotency_key=None,
):
    """
    Add a PaymentRequest to a PaymentBatch.
    Supports both legacy (Phase 1) and ledger-driven (Phase 2) creation.

    Args:
        batch_id: PaymentBatch identifier
        creator_id: User identifier (must be batch creator)
        # Legacy fields (Phase 1)
        amount: Positive decimal amount (legacy)
        currency: Three-letter currency code
        beneficiary_name: Recipient name (legacy)
        beneficiary_account: Account identifier (legacy)
        purpose: Payment purpose (legacy)
        # Phase 2: Ledger-driven fields
        entity_type: "VENDOR" or "SUBCONTRACTOR" (required for ledger-driven)
        vendor_id: Vendor UUID (required if entity_type=VENDOR)
        subcontractor_id: Subcontractor UUID (required if entity_type=SUBCONTRACTOR)
        site_id: Site UUID (required for ledger-driven)
        base_amount: Positive decimal (required for ledger-driven)
        extra_amount: Non-negative decimal (default 0)
        extra_reason: Required if extra_amount > 0
        idempotency_key: Optional idempotency key for retry safety

    Returns:
        PaymentRequest: Created request

    Raises:
        NotFoundError: If batch, creator, or ledger entities do not exist
        InvalidStateError: If batch is not DRAFT
        PermissionDeniedError: If creator is not batch creator
        ValidationError: If validation fails
    """
    from apps.users.models import User, Role, Role
    from apps.ledger.models import Vendor, Subcontractor, Site
    from apps.payments.models import IdempotencyKey

    # Idempotency check
    if idempotency_key:
        existing_key = IdempotencyKey.objects.filter(
            key=idempotency_key, operation="CREATE_PAYMENT_REQUEST"
        ).first()
        if existing_key and existing_key.target_object_id:
            try:
                return PaymentRequest.objects.get(id=existing_key.target_object_id)
            except PaymentRequest.DoesNotExist:
                pass  # Key exists but object missing, proceed with creation

    with transaction.atomic():
        try:
            batch = PaymentBatch.objects.select_for_update().get(id=batch_id)
        except PaymentBatch.DoesNotExist:
            raise NotFoundError(f"PaymentBatch {batch_id} does not exist")

        try:
            creator = User.objects.get(id=creator_id)
        except User.DoesNotExist:
            raise NotFoundError(f"User {creator_id} does not exist")

        # Check ownership
        if creator.role != Role.ADMIN and batch.created_by_id != creator_id:
            raise PermissionDeniedError("Only the batch creator can add requests")

        # Check batch state
        if batch.status != "DRAFT":
            raise InvalidStateError(
                f"Cannot add request to batch with status {batch.status}"
            )

        if is_closed_batch(batch.status):
            raise InvalidStateError("Cannot add request to closed batch")

        # Determine if legacy or ledger-driven
        is_ledger_driven = entity_type is not None

        if is_ledger_driven:
            # Phase 2: Ledger-driven validation
            if entity_type not in ("VENDOR", "SUBCONTRACTOR"):
                raise ValidationError("entity_type must be VENDOR or SUBCONTRACTOR")

            if entity_type == "VENDOR":
                if not vendor_id:
                    raise ValidationError(
                        "vendor_id is required when entity_type=VENDOR"
                    )
                if subcontractor_id:
                    raise ValidationError(
                        "Cannot specify both vendor_id and subcontractor_id"
                    )
                try:
                    vendor = Vendor.objects.select_for_update().get(
                        id=vendor_id, is_active=True
                    )
                except Vendor.DoesNotExist:
                    raise NotFoundError(f"Active Vendor {vendor_id} does not exist")
                entity_obj = vendor
                entity_name = vendor.name
            else:  # SUBCONTRACTOR
                if not subcontractor_id:
                    raise ValidationError(
                        "subcontractor_id is required when entity_type=SUBCONTRACTOR"
                    )
                if vendor_id:
                    raise ValidationError(
                        "Cannot specify both vendor_id and subcontractor_id"
                    )
                try:
                    subcontractor = Subcontractor.objects.select_for_update().get(
                        id=subcontractor_id, is_active=True
                    )
                except Subcontractor.DoesNotExist:
                    raise NotFoundError(
                        f"Active Subcontractor {subcontractor_id} does not exist"
                    )
                entity_obj = subcontractor
                entity_name = subcontractor.name

            if not site_id:
                raise ValidationError("site_id is required for ledger-driven requests")
            try:
                site = Site.objects.select_for_update().get(id=site_id, is_active=True)
            except Site.DoesNotExist:
                raise NotFoundError(f"Active Site {site_id} does not exist")

            # Amount validation
            if base_amount is None or base_amount <= 0:
                raise ValidationError("base_amount must be positive")
            if extra_amount is None:
                extra_amount = 0
            if extra_amount < 0:
                raise ValidationError("extra_amount must be non-negative")
            if extra_amount > 0 and not extra_reason:
                raise ValidationError("extra_reason is required when extra_amount > 0")

            # Compute total server-side
            total_amount = base_amount + extra_amount

            # Soft guidance: subcontractor site override warning
            if (
                entity_type == "SUBCONTRACTOR"
                and subcontractor.assigned_site_id
                and str(site_id) != str(subcontractor.assigned_site_id)
            ):
                # Create audit warning entry
                create_audit_entry(
                    event_type="SUBCONTRACTOR_SITE_OVERRIDE",
                    actor_id=creator_id,
                    entity_type="PaymentRequest",
                    entity_id=None,  # Will be set after creation
                    previous_state={
                        "assigned_site_id": str(subcontractor.assigned_site_id),
                        "assigned_site_code": subcontractor.assigned_site.code,
                    },
                    new_state={
                        "selected_site_id": str(site_id),
                        "selected_site_code": site.code,
                    },
                )

            # Validate currency
            if not currency or len(currency) != 3:
                raise ValidationError("Currency must be a three-letter code")

            # Populate snapshots (mandatory for ledger-driven)
            vendor_snapshot_name = vendor.name if entity_type == "VENDOR" else None
            subcontractor_snapshot_name = (
                subcontractor.name if entity_type == "SUBCONTRACTOR" else None
            )
            site_snapshot_code = site.code

        else:
            # Phase 1: Legacy validation
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

        # Create request
        request_data = {
            "batch": batch,
            "currency": currency.upper().strip(),
            "created_by": creator,
            "status": "DRAFT",
        }

        if is_ledger_driven:
            request_data.update(
                {
                    "amount": total_amount,  # Legacy amount field for display/constraints
                    "entity_type": entity_type,
                    "vendor": vendor if entity_type == "VENDOR" else None,
                    "subcontractor": (
                        subcontractor if entity_type == "SUBCONTRACTOR" else None
                    ),
                    "site": site,
                    "base_amount": base_amount,
                    "extra_amount": extra_amount,
                    "extra_reason": extra_reason.strip() if extra_reason else None,
                    "total_amount": total_amount,
                    "vendor_snapshot_name": vendor_snapshot_name,
                    "subcontractor_snapshot_name": subcontractor_snapshot_name,
                    "site_snapshot_code": site_snapshot_code,
                }
            )
        else:
            request_data.update(
                {
                    "amount": amount,
                    "beneficiary_name": beneficiary_name.strip(),
                    "beneficiary_account": beneficiary_account.strip(),
                    "purpose": purpose.strip(),
                }
            )

        request = PaymentRequest.objects.create(**request_data)

        # Store idempotency key if provided
        if idempotency_key:
            IdempotencyKey.objects.create(
                key=idempotency_key,
                operation="CREATE_PAYMENT_REQUEST",
                target_object_id=request.id,
                response_code=201,
            )

        # Create audit entry
        if is_ledger_driven:
            create_audit_entry(
                event_type="REQUEST_CREATED",
                actor_id=creator_id,
                entity_type="PaymentRequest",
                entity_id=request.id,
                previous_state=None,
                new_state={
                    "status": "DRAFT",
                    "entity_type": entity_type,
                    "entity_name": entity_name,
                    "site_code": site_snapshot_code,
                    "total_amount": str(total_amount),
                    "currency": request.currency,
                },
            )
        else:
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
    from apps.users.models import User, Role

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
    if creator.role != Role.ADMIN and request.batch.created_by_id != creator_id:
        raise PermissionDeniedError("Only the batch creator can update requests")

    # Check request state
    if request.status != "DRAFT":
        raise InvalidStateError(f"Cannot update request with status {request.status}")

    # Phase 2: Immutable financial lock - block modifications when APPROVED/PAID
    if request.status in ("APPROVED", "PAID"):
        raise InvalidStateError(
            "Financial fields are locked when request is APPROVED or PAID"
        )

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
    from apps.users.models import User, Role

    with transaction.atomic():
        try:
            batch = PaymentBatch.objects.select_for_update().get(id=batch_id)
        except PaymentBatch.DoesNotExist:
            raise NotFoundError(f"PaymentBatch {batch_id} does not exist")

        try:
            creator = User.objects.get(id=creator_id)
        except User.DoesNotExist:
            raise NotFoundError(f"User {creator_id} does not exist")

        # Check ownership
        if creator.role != Role.ADMIN and batch.created_by_id != creator_id:
            raise PermissionDeniedError("Only the batch creator can submit the batch")

        # Check batch state
        if batch.status != "DRAFT":
            # Idempotency: if already SUBMITTED, return success
            if batch.status == "SUBMITTED":
                return batch
            raise InvalidStateError(f"Cannot submit batch with status {batch.status}")

        # Get all requests with lock (consistent order by id)
        requests = list(
            PaymentRequest.objects.filter(batch=batch)
            .select_for_update()
            .order_by("id")
        )

        if not requests:
            raise PreconditionFailedError(
                "Batch must contain at least one payment request"
            )

        # Validate all requests are DRAFT
        for req in requests:
            if req.status != "DRAFT":
                raise InvalidStateError(
                    f"All requests must be DRAFT. Request {req.id} has status {req.status}"
                )

            # Validate request data (support both legacy and ledger-driven)
            if req.entity_type:
                # Ledger-driven validation
                if not req.total_amount or req.total_amount <= 0:
                    raise PreconditionFailedError(
                        f"Request {req.id} has invalid total_amount"
                    )
                if not req.site_id:
                    raise PreconditionFailedError(
                        f"Request {req.id} is missing site (ledger-driven)"
                    )
            else:
                # Legacy validation
                if req.amount <= 0:
                    raise PreconditionFailedError(
                        f"Request {req.id} has invalid amount"
                    )
                if (
                    not req.beneficiary_name
                    or not req.beneficiary_account
                    or not req.purpose
                ):
                    raise PreconditionFailedError(
                        f"Request {req.id} has missing required fields"
                    )

            if not req.currency or len(req.currency) != 3:
                raise PreconditionFailedError(f"Request {req.id} has invalid currency")

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
    from apps.users.models import User, Role

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
    if creator.role != Role.ADMIN and batch.created_by_id != creator_id:
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


def approve_request(request_id, approver_id, comment=None, idempotency_key=None):
    """
    Approve a PaymentRequest (PENDING_APPROVAL only).

    Args:
        request_id: PaymentRequest identifier
        approver_id: User identifier (must have APPROVER role)
        comment: Optional comment
        idempotency_key: Optional idempotency key for retry safety

    Returns:
        PaymentRequest: Updated request

    Raises:
        NotFoundError: If request or approver does not exist
        InvalidStateError: If request is not PENDING_APPROVAL
        PermissionDeniedError: If approver does not have APPROVER role
        PreconditionFailedError: If ApprovalRecord already exists
    """
    from apps.users.models import User, Role
    from apps.payments.models import IdempotencyKey

    # Idempotency check
    if idempotency_key:
        existing_key = IdempotencyKey.objects.filter(
            key=idempotency_key, operation="APPROVE_PAYMENT_REQUEST"
        ).first()
        if existing_key and existing_key.target_object_id:
            try:
                return PaymentRequest.objects.get(id=existing_key.target_object_id)
            except PaymentRequest.DoesNotExist:
                pass  # Key exists but object missing, proceed with approval

    with transaction.atomic():
        try:
            request = PaymentRequest.objects.select_for_update().get(id=request_id)
        except PaymentRequest.DoesNotExist:
            raise NotFoundError(f"PaymentRequest {request_id} does not exist")

        try:
            approver = User.objects.get(id=approver_id)
        except User.DoesNotExist:
            raise NotFoundError(f"User {approver_id} does not exist")

        # Check role (ADMIN can approve as well)
        if approver.role not in (Role.APPROVER, Role.ADMIN):
            raise PermissionDeniedError(
                "Only users with APPROVER or ADMIN role can approve requests"
            )

        # Check request state
        if request.status != "PENDING_APPROVAL":
            if request.status == "APPROVED":
                # Idempotency: same key = return success (retry); different key = block
                if idempotency_key:
                    existing = IdempotencyKey.objects.filter(
                        key=idempotency_key, operation="APPROVE_PAYMENT_REQUEST"
                    ).first()
                    if existing and existing.target_object_id:
                        return request
                raise InvalidStateError("Request has already been approved")
            raise InvalidStateError(
                f"Cannot approve request with status {request.status}"
            )

        # Create ApprovalRecord
        ApprovalRecord.objects.create(
            payment_request=request,
            approver=approver,
            decision="APPROVED",
            comment=comment.strip() if comment else None,
        )

        # Transition request to APPROVED with version locking
        validate_transition("PaymentRequest", request.status, "APPROVED")
        current_version = request.version
        updated_count = version_locked_update(
            PaymentRequest.objects.filter(
                id=request_id, status="PENDING_APPROVAL", version=current_version
            ),
            current_version=current_version,
            status="APPROVED",
            updated_by=approver,
        )
        if updated_count == 0:
            raise InvalidStateError(
                "Concurrent modification detected or invalid state for approval"
            )
        request.refresh_from_db()

        # Store idempotency key if provided
        if idempotency_key:
            IdempotencyKey.objects.create(
                key=idempotency_key,
                operation="APPROVE_PAYMENT_REQUEST",
                target_object_id=request.id,
                response_code=200,
            )

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


def reject_request(request_id, approver_id, comment=None, idempotency_key=None):
    """
    Reject a PaymentRequest (PENDING_APPROVAL only).

    Args:
        request_id: PaymentRequest identifier
        approver_id: User identifier (must have APPROVER role)
        comment: Optional comment
        idempotency_key: Optional idempotency key for retry safety

    Returns:
        PaymentRequest: Updated request

    Raises:
        NotFoundError: If request or approver does not exist
        InvalidStateError: If request is not PENDING_APPROVAL
        PermissionDeniedError: If approver does not have APPROVER role
        PreconditionFailedError: If ApprovalRecord already exists
    """
    from apps.users.models import User, Role
    from apps.payments.models import IdempotencyKey

    # Idempotency check
    if idempotency_key:
        existing_key = IdempotencyKey.objects.filter(
            key=idempotency_key, operation="REJECT_PAYMENT_REQUEST"
        ).first()
        if existing_key and existing_key.target_object_id:
            try:
                return PaymentRequest.objects.get(id=existing_key.target_object_id)
            except PaymentRequest.DoesNotExist:
                pass  # Key exists but object missing, proceed with rejection

    try:
        request = PaymentRequest.objects.select_for_update().get(id=request_id)
    except PaymentRequest.DoesNotExist:
        raise NotFoundError(f"PaymentRequest {request_id} does not exist")

    try:
        approver = User.objects.get(id=approver_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {approver_id} does not exist")

    # Check role (ADMIN can reject as well)
    if approver.role not in (Role.APPROVER, Role.ADMIN):
        raise PermissionDeniedError(
            "Only users with APPROVER or ADMIN role can reject requests"
        )

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
        # Set transaction isolation level for financial operations
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        # Create ApprovalRecord
        ApprovalRecord.objects.create(
            payment_request=request,
            approver=approver,
            decision="REJECTED",
            comment=comment.strip() if comment else None,
        )

        # Transition request to REJECTED with version locking
        validate_transition("PaymentRequest", request.status, "REJECTED")
        current_version = request.version
        updated_count = version_locked_update(
            PaymentRequest.objects.filter(
                id=request_id, status="PENDING_APPROVAL", version=current_version
            ),
            current_version=current_version,
            status="REJECTED",
            updated_by=approver,
        )
        if updated_count == 0:
            raise InvalidStateError(
                "Concurrent modification detected or invalid state for rejection"
            )
        request.refresh_from_db()

        # Store idempotency key if provided
        if idempotency_key:
            IdempotencyKey.objects.create(
                key=idempotency_key,
                operation="REJECT_PAYMENT_REQUEST",
                target_object_id=request.id,
                response_code=200,
            )

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


def mark_paid(request_id, actor_id, idempotency_key=None):
    """
    Mark a PaymentRequest as PAID (APPROVED only).

    Args:
        request_id: PaymentRequest identifier
        actor_id: User identifier (must have CREATOR or APPROVER role)
        idempotency_key: Optional idempotency key for retry safety

    Returns:
        PaymentRequest: Updated request

    Raises:
        NotFoundError: If request or actor does not exist
        InvalidStateError: If request is not APPROVED
        PermissionDeniedError: If actor does not have required role
    """
    from apps.users.models import User, Role
    from apps.payments.models import IdempotencyKey

    # Idempotency check
    if idempotency_key:
        existing_key = IdempotencyKey.objects.filter(
            key=idempotency_key, operation="MARK_PAYMENT_PAID"
        ).first()
        if existing_key and existing_key.target_object_id:
            try:
                return PaymentRequest.objects.get(id=existing_key.target_object_id)
            except PaymentRequest.DoesNotExist:
                pass  # Key exists but object missing, proceed with mark_paid

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
        # Set transaction isolation level for financial operations
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        # Transition request to PAID with version locking
        validate_transition("PaymentRequest", request.status, "PAID")
        current_version = request.version
        updated_count = version_locked_update(
            PaymentRequest.objects.filter(
                id=request_id, status="APPROVED", version=current_version
            ),
            current_version=current_version,
            status="PAID",
            updated_by=actor,
        )
        if updated_count == 0:
            raise InvalidStateError(
                "Concurrent modification detected or invalid state for mark_paid"
            )
        request.refresh_from_db()

        # Store idempotency key if provided
        if idempotency_key:
            IdempotencyKey.objects.create(
                key=idempotency_key,
                operation="MARK_PAYMENT_PAID",
                target_object_id=request.id,
                response_code=200,
            )

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
    from apps.users.models import User, Role
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
    if creator.role != Role.ADMIN and request.batch.created_by_id != creator_id:
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
