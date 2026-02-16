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
    """Serializer for PaymentRequest."""

    id = serializers.UUIDField(read_only=True)
    batchId = serializers.UUIDField(source="batch_id", read_only=True)
    beneficiaryName = serializers.CharField(source="beneficiary_name")
    beneficiaryAccount = serializers.CharField(source="beneficiary_account")
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
            "amount",
            "currency",
            "beneficiaryName",
            "beneficiaryAccount",
            "purpose",
            "status",
            "createdAt",
            "createdBy",
            "updatedAt",
            "updatedBy",
        ]
        read_only_fields = [
            "id",
            "status",
            "createdAt",
            "createdBy",
            "updatedAt",
            "updatedBy",
        ]


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
            if soa.version_number == 1:
                uploader = soa.uploaded_by.display_name or soa.uploaded_by.username
                change_summary = (
                    f"Initial upload by {uploader} "
                    f"on {soa.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                uploader = soa.uploaded_by.display_name or soa.uploaded_by.username
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
                    "uploadedBy": str(soa.uploaded_by_id),
                    "uploadedByName": soa.uploaded_by.display_name
                    or soa.uploaded_by.username,
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
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = PaymentRequest
        fields = [
            "id",
            "batchId",
            "batchTitle",
            "amount",
            "currency",
            "beneficiaryName",
            "purpose",
            "status",
            "createdAt",
        ]


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
        from django.db.models import Sum

        total = obj.requests.aggregate(total=Sum("amount"))["total"]
        return str(total) if total is not None else "0"

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
    uploadedBy = serializers.UUIDField(source="uploaded_by_id", read_only=True)

    class Meta:
        model = SOAVersion
        fields = [
            "id",
            "requestId",
            "versionNumber",
            "documentReference",
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
