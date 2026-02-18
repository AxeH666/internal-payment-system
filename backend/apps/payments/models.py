"""
Payment domain models: PaymentBatch, PaymentRequest, ApprovalRecord, SOAVersion.

All models follow the domain model specification (02_DOMAIN_MODEL.md).
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator


class PaymentBatch(models.Model):
    """PaymentBatch model - logical grouping of payment requests."""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="created_batches"
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payment_batches"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    status__in=[
                        "DRAFT",
                        "SUBMITTED",
                        "PROCESSING",
                        "COMPLETED",
                        "CANCELLED",
                    ]
                ),
                name="valid_batch_status",
            ),
            # submitted_at NOT NULL when status != 'DRAFT'
            models.CheckConstraint(
                check=models.Q(status="DRAFT") | models.Q(submitted_at__isnull=False),
                name="submitted_at_set_when_not_draft",
            ),
            # completed_at NOT NULL when status IN ('COMPLETED', 'CANCELLED')
            models.CheckConstraint(
                check=models.Q(status__in=["DRAFT", "SUBMITTED", "PROCESSING"])
                | models.Q(completed_at__isnull=False),
                name="completed_at_set_when_closed",
            ),
        ]
        indexes = [
            models.Index(fields=["status"], name="idx_batch_status"),
            models.Index(fields=["created_by"], name="idx_batch_created_by"),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"


class PaymentRequest(models.Model):
    """PaymentRequest model - single payment instruction within a batch."""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("PENDING_APPROVAL", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("PAID", "Paid"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        PaymentBatch, on_delete=models.PROTECT, related_name="requests"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True,
    )  # Nullable for ledger-driven (uses total_amount)
    currency = models.CharField(max_length=3)  # ISO 4217 three-letter code
    beneficiary_name = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_account = models.CharField(max_length=255, null=True, blank=True)
    purpose = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="created_requests"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_requests",
    )
    # Phase 2: Ledger-driven payment fields (nullable for legacy compatibility)
    entity_type = models.CharField(
        max_length=20,
        choices=[("VENDOR", "Vendor"), ("SUBCONTRACTOR", "Subcontractor")],
        null=True,
        blank=True,
    )
    vendor = models.ForeignKey(
        "ledger.Vendor",
        on_delete=models.PROTECT,
        related_name="payment_requests",
        null=True,
        blank=True,
    )
    subcontractor = models.ForeignKey(
        "ledger.Subcontractor",
        on_delete=models.PROTECT,
        related_name="payment_requests",
        null=True,
        blank=True,
    )
    site = models.ForeignKey(
        "ledger.Site",
        on_delete=models.PROTECT,
        related_name="payment_requests",
        null=True,
        blank=True,
    )
    # Phase 2: Amount breakdown fields (nullable for legacy compatibility)
    base_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True,
    )
    extra_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
    )
    extra_reason = models.TextField(null=True, blank=True)
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True,
    )
    # Phase 2: Snapshot fields for historical preservation (nullable for legacy)
    vendor_snapshot_name = models.CharField(max_length=255, null=True, blank=True)
    site_snapshot_code = models.CharField(max_length=100, null=True, blank=True)
    subcontractor_snapshot_name = models.CharField(
        max_length=255, null=True, blank=True
    )
    # Phase 2: Version locking and execution tracking
    version = models.IntegerField(default=1)
    execution_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "payment_requests"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    status__in=[
                        "DRAFT",
                        "SUBMITTED",
                        "PENDING_APPROVAL",
                        "APPROVED",
                        "REJECTED",
                        "PAID",
                    ]
                ),
                name="valid_request_status",
            ),
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="amount_positive"
            ),
            # Phase 2: Legacy vs LedgerDriven mutual exclusivity
            models.CheckConstraint(
                check=models.Q(
                    (
                        models.Q(entity_type__isnull=True)
                        & models.Q(beneficiary_name__isnull=False)
                    )
                    | (
                        models.Q(entity_type__isnull=False)
                        & models.Q(beneficiary_name__isnull=True)
                    )
                ),
                name="legacy_or_ledger_exclusive",
            ),
            # Phase 2: Vendor/Subcontractor FK exclusivity
            models.CheckConstraint(
                check=models.Q(
                    (
                        models.Q(vendor_id__isnull=False)
                        & models.Q(subcontractor_id__isnull=True)
                    )
                    | (
                        models.Q(vendor_id__isnull=True)
                        & models.Q(subcontractor_id__isnull=False)
                    )
                    | (
                        models.Q(vendor_id__isnull=True)
                        & models.Q(subcontractor_id__isnull=True)
                    )  # legacy
                ),
                name="vendor_or_subcontractor_exclusive",
            ),
            # Phase 2: total_amount integrity (when not null)
            models.CheckConstraint(
                check=models.Q(total_amount__isnull=True)
                | models.Q(
                    total_amount=models.F("base_amount") + models.F("extra_amount")
                ),
                name="total_amount_integrity",
            ),
        ]
        indexes = [
            models.Index(fields=["batch"], name="idx_request_batch"),
            models.Index(fields=["status"], name="idx_request_status"),
            models.Index(fields=["batch", "status"], name="idx_request_batch_status"),
            models.Index(fields=["status", "batch"], name="idx_request_status_batch"),
            models.Index(fields=["execution_id"], name="idx_request_execution_id"),
        ]

    def __str__(self):
        name = (
            self.beneficiary_name
            or self.vendor_snapshot_name
            or self.subcontractor_snapshot_name
            or "Unknown"
        )
        amt = self.amount or self.total_amount or 0
        return f"{name} - {amt} {self.currency} ({self.status})"


class ApprovalRecord(models.Model):
    """ApprovalRecord model - record of approval or rejection action."""

    DECISION_CHOICES = [
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_request = models.OneToOneField(
        PaymentRequest, on_delete=models.PROTECT, related_name="approval"
    )
    approver = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="approval_records"
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "approval_records"
        constraints = [
            models.CheckConstraint(
                check=models.Q(decision__in=["APPROVED", "REJECTED"]),
                name="valid_decision",
            ),
        ]
        indexes = [
            models.Index(fields=["payment_request"], name="idx_approval_request"),
        ]

    def __str__(self):
        return f"{self.payment_request} - {self.decision} by {self.approver}"


class SOAVersion(models.Model):
    """SOAVersion model - versioned snapshot of Statement of Account document."""

    SOURCE_UPLOAD = "UPLOAD"
    SOURCE_GENERATED = "GENERATED"
    SOURCE_CHOICES = [
        (SOURCE_UPLOAD, "Upload"),
        (SOURCE_GENERATED, "Generated"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_request = models.ForeignKey(
        PaymentRequest, on_delete=models.PROTECT, related_name="soa_versions"
    )
    version_number = models.PositiveIntegerField()
    document_reference = models.CharField(max_length=512)  # Storage path or identifier
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_UPLOAD,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="uploaded_soas",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "soa_versions"
        constraints = [
            models.CheckConstraint(
                check=models.Q(version_number__gte=1), name="version_number_positive"
            ),
            models.UniqueConstraint(
                fields=["payment_request", "version_number"],
                name="unique_request_version",
            ),
        ]
        indexes = [
            models.Index(fields=["payment_request"], name="idx_soa_request"),
        ]

    def __str__(self):
        return f"SOA v{self.version_number} for {self.payment_request}"


class IdempotencyKey(models.Model):
    """Idempotency key for preventing duplicate financial operations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, db_index=True)
    operation = models.CharField(max_length=100)
    target_object_id = models.UUIDField(null=True)
    response_code = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idempotency_keys"
        constraints = [
            models.UniqueConstraint(
                fields=["key", "operation"], name="unique_idempotency_per_operation"
            )
        ]
        indexes = [
            models.Index(fields=["key"], name="idx_idempotency_key"),
        ]

    def __str__(self):
        return f"{self.operation}:{self.key}"
