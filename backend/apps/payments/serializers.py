"""
Serializers for payment models.

No business logic in serializers - validation only.
All mutations flow through service layer.
"""

from rest_framework import serializers
from apps.payments.models import (
    PaymentBatch,
    PaymentRequest,
    SOAVersion,
)


class PaymentRequestSerializer(serializers.ModelSerializer):
    """Serializer for PaymentRequest with Phase 2 fields."""

    id = serializers.UUIDField(read_only=True)
    batchId = serializers.UUIDField(source="batch_id", read_only=True)
    # Legacy fields (Phase 1)
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True
    )
    beneficiaryName = serializers.CharField(
        source="beneficiary_name", required=False, allow_null=True
    )
    beneficiaryAccount = serializers.CharField(
        source="beneficiary_account", required=False, allow_null=True
    )
    purpose = serializers.CharField(required=False, allow_null=True)
    # Phase 2: Ledger-driven fields
    entityType = serializers.CharField(
        source="entity_type", required=False, allow_null=True
    )
    vendorId = serializers.UUIDField(
        source="vendor_id", required=False, allow_null=True
    )
    subcontractorId = serializers.UUIDField(
        source="subcontractor_id", required=False, allow_null=True
    )
    siteId = serializers.UUIDField(source="site_id", required=False, allow_null=True)
    baseAmount = serializers.DecimalField(
        source="base_amount",
        max_digits=15,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    extraAmount = serializers.DecimalField(
        source="extra_amount",
        max_digits=15,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    extraReason = serializers.CharField(
        source="extra_reason", required=False, allow_null=True
    )
    totalAmount = serializers.DecimalField(
        source="total_amount", max_digits=15, decimal_places=2, read_only=True
    )
    # Phase 2: Snapshot fields (read-only, display-safe)
    vendorSnapshotName = serializers.CharField(
        source="vendor_snapshot_name", read_only=True, allow_null=True
    )
    siteSnapshotCode = serializers.CharField(
        source="site_snapshot_code", read_only=True, allow_null=True
    )
    subcontractorSnapshotName = serializers.CharField(
        source="subcontractor_snapshot_name", read_only=True, allow_null=True
    )
    entityName = serializers.SerializerMethodField()
    # Phase 2: Version and execution tracking
    version = serializers.IntegerField(read_only=True)
    executionId = serializers.UUIDField(
        source="execution_id", read_only=True, allow_null=True
    )
    # Common fields
    currency = serializers.CharField(required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    createdBy = serializers.UUIDField(source="created_by_id", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    updatedBy = serializers.UUIDField(
        source="updated_by_id", read_only=True, allow_null=True
    )

    class Meta:
        model = PaymentRequest
        fields = [
            "id",
            "batchId",
            # Legacy fields
            "amount",
            "currency",
            "beneficiaryName",
            "beneficiaryAccount",
            "purpose",
            # Phase 2 fields
            "entityType",
            "vendorId",
            "subcontractorId",
            "siteId",
            "baseAmount",
            "extraAmount",
            "extraReason",
            "totalAmount",
            "vendorSnapshotName",
            "siteSnapshotCode",
            "subcontractorSnapshotName",
            "entityName",
            "version",
            "executionId",
            # Status and timestamps
            "status",
            "createdAt",
            "createdBy",
            "updatedAt",
            "updatedBy",
        ]
        read_only_fields = [
            "id",
            "status",
            "totalAmount",
            "vendorSnapshotName",
            "siteSnapshotCode",
            "subcontractorSnapshotName",
            "entityName",
            "version",
            "executionId",
            "createdAt",
            "createdBy",
            "updatedAt",
            "updatedBy",
        ]

    def get_entityName(self, obj):
        """Get entity name (display-safe, no business rules)."""
        if obj.entity_type == "VENDOR" and obj.vendor_snapshot_name:
            return obj.vendor_snapshot_name
        elif obj.entity_type == "SUBCONTRACTOR" and obj.subcontractor_snapshot_name:
            return obj.subcontractor_snapshot_name
        return None


class PaymentRequestDetailSerializer(PaymentRequestSerializer):
    """Serializer for PaymentRequest detail with approval and SOA versions."""

    approval = serializers.SerializerMethodField()
    soaVersions = serializers.SerializerMethodField()

    class Meta(PaymentRequestSerializer.Meta):
        fields = PaymentRequestSerializer.Meta.fields + ["approval", "soaVersions"]

    def get_approval(self, obj):
        """Get approval record if exists."""
        if hasattr(obj, "approval"):
            approval = obj.approval
            return {
                "decision": approval.decision,
                "comment": approval.comment,
                "approverId": str(approval.approver_id),
                "createdAt": approval.created_at.isoformat(),
            }
        return None

    def get_soaVersions(self, obj):
        """Get SOA versions with change summary (version header)."""
        soas = obj.soa_versions.select_related("uploaded_by").order_by("version_number")
        result = []
        for soa in soas:
            uploader = (
                (soa.uploaded_by.display_name or soa.uploaded_by.username)
                if soa.uploaded_by
                else "System"
            )
            if soa.version_number == 1:
                change_summary = (
                    f"Initial upload by {uploader} "
                    f"on {soa.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                prev_v = soa.version_number - 1
                change_summary = (
                    f"Version {soa.version_number} - Replaces v{prev_v}, "
                    f"uploaded by {uploader} "
                    f"on {soa.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
                )
            result.append(
                {
                    "id": str(soa.id),
                    "versionNumber": soa.version_number,
                    "uploadedAt": soa.uploaded_at.isoformat(),
                    "uploadedBy": (
                        str(soa.uploaded_by_id) if soa.uploaded_by_id else None
                    ),
                    "uploadedByName": uploader,
                    "source": soa.source,
                    "changeSummary": change_summary,
                    "downloadUrl": (
                        f"/api/v1/batches/{obj.batch_id}/requests/{obj.id}/"
                        f"soa/{soa.id}/download"
                    ),
                }
            )
        return result


class PaymentRequestListSerializer(serializers.ModelSerializer):
    """Serializer for payment request list (approval queue)."""

    id = serializers.UUIDField(read_only=True)
    batchId = serializers.UUIDField(source="batch_id", read_only=True)
    batchTitle = serializers.CharField(source="batch.title", read_only=True)
    beneficiaryName = serializers.CharField(source="beneficiary_name", read_only=True)
    entityName = serializers.SerializerMethodField()
    totalAmount = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = PaymentRequest
        fields = [
            "id",
            "batchId",
            "batchTitle",
            "amount",
            "totalAmount",
            "currency",
            "beneficiaryName",
            "entityName",
            "purpose",
            "status",
            "createdAt",
        ]

    def get_entityName(self, obj):
        """Get entity name (display-safe)."""
        if obj.entity_type == "VENDOR" and obj.vendor_snapshot_name:
            return obj.vendor_snapshot_name
        elif obj.entity_type == "SUBCONTRACTOR" and obj.subcontractor_snapshot_name:
            return obj.subcontractor_snapshot_name
        return None

    def get_totalAmount(self, obj):
        """Get total amount (ledger-driven) or amount (legacy)."""
        if obj.total_amount is not None:
            return str(obj.total_amount)
        elif obj.amount is not None:
            return str(obj.amount)
        return None


class PaymentBatchSerializer(serializers.ModelSerializer):
    """Serializer for PaymentBatch."""

    id = serializers.UUIDField(read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    createdBy = serializers.UUIDField(source="created_by_id", read_only=True)
    submittedAt = serializers.DateTimeField(
        source="submitted_at", read_only=True, allow_null=True
    )
    completedAt = serializers.DateTimeField(
        source="completed_at", read_only=True, allow_null=True
    )
    requestCount = serializers.SerializerMethodField()

    class Meta:
        model = PaymentBatch
        fields = [
            "id",
            "title",
            "status",
            "createdAt",
            "createdBy",
            "submittedAt",
            "completedAt",
            "requestCount",
        ]
        read_only_fields = [
            "id",
            "status",
            "createdAt",
            "createdBy",
            "submittedAt",
            "completedAt",
            "requestCount",
        ]

    def get_requestCount(self, obj):
        """Get count of requests in batch."""
        return obj.requests.count()


class PaymentBatchDetailSerializer(PaymentBatchSerializer):
    """Serializer for batch detail with requests, totals, Live SOA."""

    requests = PaymentRequestSerializer(many=True, read_only=True)
    batchTotal = serializers.SerializerMethodField()
    liveSoaSummary = serializers.SerializerMethodField()

    class Meta(PaymentBatchSerializer.Meta):
        fields = PaymentBatchSerializer.Meta.fields + [
            "requests",
            "batchTotal",
            "liveSoaSummary",
        ]

    def get_batchTotal(self, obj):
        """Compute sum of request amounts (totals validation)."""
        from django.db.models import Sum, Q
        from decimal import Decimal

        # Sum total_amount where present (ledger-driven), else amount (legacy)
        total = Decimal("0")
        for req in obj.requests.all():
            if req.total_amount is not None:
                total += req.total_amount
            elif req.amount is not None:
                total += req.amount
        return str(total)

    def get_liveSoaSummary(self, obj):
        """Live SOA view: computed latest SOA status per request."""
        summary = []
        requests = obj.requests.prefetch_related("soa_versions").all()
        for req in requests:
            soas = list(req.soa_versions.all().order_by("-version_number"))
            latest = soas[0] if soas else None
            summary.append(
                {
                    "requestId": str(req.id),
                    "beneficiaryName": req.beneficiary_name,
                    "amount": str(req.amount),
                    "currency": req.currency,
                    "hasSoa": len(soas) > 0,
                    "latestVersion": latest.version_number if latest else None,
                    "latestUploadedAt": (
                        latest.uploaded_at.isoformat() if latest else None
                    ),
                }
            )
        return summary


class ApprovalRequestSerializer(serializers.Serializer):
    """Serializer for approve/reject request body."""

    comment = serializers.CharField(required=False, allow_blank=True)


class SOAVersionSerializer(serializers.ModelSerializer):
    """Serializer for SOAVersion."""

    id = serializers.UUIDField(read_only=True)
    requestId = serializers.UUIDField(source="payment_request_id", read_only=True)
    versionNumber = serializers.IntegerField(source="version_number", read_only=True)
    documentReference = serializers.CharField(
        source="document_reference", read_only=True
    )
    uploadedAt = serializers.DateTimeField(source="uploaded_at", read_only=True)
    uploadedBy = serializers.UUIDField(
        source="uploaded_by_id", read_only=True, allow_null=True
    )

    class Meta:
        model = SOAVersion
        fields = [
            "id",
            "requestId",
            "versionNumber",
            "documentReference",
            "source",
            "uploadedAt",
            "uploadedBy",
        ]


class SOAVersionDetailSerializer(SOAVersionSerializer):
    """Serializer for SOAVersion detail with download URL."""

    downloadUrl = serializers.SerializerMethodField()

    class Meta(SOAVersionSerializer.Meta):
        fields = SOAVersionSerializer.Meta.fields + ["downloadUrl"]

    def get_downloadUrl(self, obj):
        """Generate download URL for SOA document."""
        # In production, generate signed URL or use proper storage backend
        return (
            f"/api/v1/batches/{obj.payment_request.batch_id}/requests/"
            f"{obj.payment_request_id}/soa/{obj.id}/download"
        )
