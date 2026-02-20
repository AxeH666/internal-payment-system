"""
Payment API views.

All mutations flow through service layer.
All endpoints define permission_classes per API contract.
"""

import logging

from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from core.exceptions import DomainError
from core.permissions import (
    IsCreator,
    IsApprover,
    IsCreatorOrApprover,
    IsAuthenticatedReadOnly,
)
from apps.payments.models import PaymentBatch, PaymentRequest, SOAVersion
from apps.payments import services
from apps.payments.serializers import (
    PaymentBatchSerializer,
    PaymentBatchDetailSerializer,
    PaymentRequestSerializer,
    PaymentRequestDetailSerializer,
    PaymentRequestListSerializer,
    ApprovalRequestSerializer,
    SOAVersionSerializer,
    SOAVersionDetailSerializer,
)

logger = logging.getLogger(__name__)


@api_view(["POST", "GET"])
def create_or_list_batches(request):
    """
    POST /api/v1/batches - Create a new PaymentBatch
    GET /api/v1/batches - List PaymentBatches
    """
    if request.method == "POST":
        # Check permission for POST
        if not IsCreator().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Accept both "title" and "name" for compatibility
        title = request.data.get("title") or request.data.get("name")

        if not title or not title.strip():
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Title must be non-empty",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            batch = services.create_batch(request.user.id, title)
            serializer = PaymentBatchSerializer(batch)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
        except DomainError:
            raise
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "Batch creation conflict (e.g. duplicate)",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

    else:  # GET
        # Check permission for GET
        if not IsAuthenticatedReadOnly().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        status_filter = request.query_params.get("status")

        queryset = PaymentBatch.objects.all().order_by("-created_at")

        if status_filter:
            if status_filter not in [
                "DRAFT",
                "SUBMITTED",
                "PROCESSING",
                "COMPLETED",
                "CANCELLED",
            ]:
                return Response(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid status filter",
                            "details": {},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_filter)

        paginator = LimitOffsetPagination()
        paginator.default_limit = 50
        paginator.max_limit = 100

        page = paginator.paginate_queryset(queryset, request)
        serializer = PaymentBatchSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def get_batch(request, batchId):
    """
    GET /api/v1/batches/{batchId}

    Get PaymentBatch detail with requests.
    """
    try:
        batch = PaymentBatch.objects.prefetch_related(
            "requests", "requests__soa_versions"
        ).get(id=batchId)
    except PaymentBatch.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"PaymentBatch {batchId} does not exist",
                    "details": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = PaymentBatchDetailSerializer(batch)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsCreator])
def submit_batch(request, batchId):
    """
    POST /api/v1/batches/{batchId}/submit

    Submit a PaymentBatch and transition all requests.
    """
    try:
        batch = services.submit_batch(batchId, request.user.id)
        serializer = PaymentBatchDetailSerializer(batch)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except IntegrityError:
        return Response(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": "Batch state conflict",
                    "details": {},
                }
            },
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST"])
@permission_classes([IsCreator])
def cancel_batch(request, batchId):
    """
    POST /api/v1/batches/{batchId}/cancel

    Cancel a PaymentBatch (DRAFT only).
    """
    try:
        batch = services.cancel_batch(batchId, request.user.id)
        serializer = PaymentBatchSerializer(batch)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except IntegrityError:
        return Response(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": "Batch state conflict",
                    "details": {},
                }
            },
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST"])
@permission_classes([IsCreator])
def add_request(request, batchId):
    """
    POST /api/v1/batches/{batchId}/requests

    Add a PaymentRequest to a PaymentBatch.
    Supports both legacy (Phase 1) and ledger-driven (Phase 2) creation.
    """
    from decimal import Decimal, InvalidOperation

    logger.debug("add_request invoked", extra={"batchId": str(batchId)})
    # Phase 2: Ledger-driven fields
    entity_type = request.data.get("entityType")
    vendor_id = request.data.get("vendorId")
    subcontractor_id = request.data.get("subcontractorId")
    site_id = request.data.get("siteId")
    base_amount = request.data.get("baseAmount")
    extra_amount = request.data.get("extraAmount")
    extra_reason = request.data.get("extraReason")

    # Legacy fields (Phase 1)
    amount = request.data.get("amount")
    currency = request.data.get("currency")
    beneficiary_name = request.data.get("beneficiaryName")
    beneficiary_account = request.data.get("beneficiaryAccount")
    purpose = request.data.get("purpose")

    # Convert decimal fields
    try:
        if amount is not None:
            amount = Decimal(str(amount))
        if base_amount is not None:
            base_amount = Decimal(str(base_amount))
        if extra_amount is not None:
            extra_amount = Decimal(str(extra_amount))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid amount format",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Ignore client-provided totalAmount (server computes it)
    # This ensures tamper protection
    if "totalAmount" in request.data:
        pass  # Silently ignore - server will compute

    try:
        payment_request = services.add_request(
            batchId,
            request.user.id,
            # Legacy fields
            amount=amount,
            currency=currency,
            beneficiary_name=beneficiary_name,
            beneficiary_account=beneficiary_account,
            purpose=purpose,
            # Phase 2 fields
            entity_type=entity_type,
            vendor_id=vendor_id,
            subcontractor_id=subcontractor_id,
            site_id=site_id,
            base_amount=base_amount,
            extra_amount=extra_amount,
            extra_reason=extra_reason,
            idempotency_key=getattr(request, "idempotency_key", None),
        )
        serializer = PaymentRequestSerializer(payment_request)
        return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
    except DomainError:
        raise
    except IntegrityError:
        return Response(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": "Request creation conflict (idempotency or duplicate)",
                    "details": {},
                }
            },
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["GET", "PATCH"])
def get_or_update_request(request, batchId, requestId):
    """
    GET /api/v1/batches/{batchId}/requests/{requestId}
    PATCH /api/v1/batches/{batchId}/requests/{requestId}

    Get or update PaymentRequest.
    """
    if request.method == "GET":
        permission_classes = [IsAuthenticatedReadOnly]
    else:  # PATCH
        permission_classes = [IsCreator]

    # Check permissions
    for permission_class in permission_classes:
        if not permission_class().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    if request.method == "GET":
        try:
            payment_request = (
                PaymentRequest.objects.select_related("approval", "approval__approver")
                .prefetch_related("soa_versions")
                .get(id=requestId, batch_id=batchId)
            )
        except PaymentRequest.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"PaymentRequest {requestId} does not exist",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PaymentRequestDetailSerializer(payment_request)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    else:  # PATCH
        update_fields = {}

        if "amount" in request.data:
            try:
                from decimal import Decimal

                update_fields["amount"] = Decimal(str(request.data["amount"]))
            except (ValueError, TypeError):
                return Response(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid amount format",
                            "details": {},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if "currency" in request.data:
            update_fields["currency"] = request.data["currency"]

        if "beneficiaryName" in request.data:
            update_fields["beneficiary_name"] = request.data["beneficiaryName"]

        if "beneficiaryAccount" in request.data:
            update_fields["beneficiary_account"] = request.data["beneficiaryAccount"]

        if "purpose" in request.data:
            update_fields["purpose"] = request.data["purpose"]

        try:
            payment_request = services.update_request(
                requestId, batchId, request.user.id, **update_fields
            )
            serializer = PaymentRequestSerializer(payment_request)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except DomainError as e:
            # Map domain errors to 4xx in-view so PATCH_AFTER_APPROVE always returns 409
            _status = (
                status.HTTP_409_CONFLICT
                if e.code == "INVALID_STATE"
                else (
                    status.HTTP_404_NOT_FOUND
                    if e.code == "NOT_FOUND"
                    else (
                        status.HTTP_403_FORBIDDEN
                        if e.code == "FORBIDDEN"
                        else status.HTTP_400_BAD_REQUEST
                    )
                )
            )
            return Response(
                {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details,
                    }
                },
                status=_status,
            )
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "Cannot update request in current state",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def get_request(request, requestId):
    """
    GET /api/v1/requests/{requestId}

    Get PaymentRequest by ID (standalone endpoint for approval queue).
    """
    try:
        payment_request = (
            PaymentRequest.objects.select_related(
                "approval", "approval__approver", "batch"
            )
            .prefetch_related("soa_versions")
            .get(id=requestId)
        )
    except PaymentRequest.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"PaymentRequest {requestId} does not exist",
                    "details": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = PaymentRequestDetailSerializer(payment_request)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsApprover])
def list_pending_requests(request):
    """
    GET /api/v1/requests

    List PaymentRequests for approval queue.
    """
    status_filter = request.query_params.get("status", "PENDING_APPROVAL")

    if status_filter not in [
        "DRAFT",
        "SUBMITTED",
        "PENDING_APPROVAL",
        "APPROVED",
        "REJECTED",
        "PAID",
    ]:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid status filter",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    queryset = (
        PaymentRequest.objects.select_related("batch")
        .filter(status=status_filter)
        .order_by("-created_at")
    )

    paginator = LimitOffsetPagination()
    paginator.default_limit = 50
    paginator.max_limit = 100

    page = paginator.paginate_queryset(queryset, request)
    serializer = PaymentRequestListSerializer(page, many=True)

    return paginator.get_paginated_response(serializer.data)


@api_view(["POST"])
@permission_classes([IsApprover])
def approve_request(request, requestId):
    """
    POST /api/v1/requests/{requestId}/approve

    Approve a PaymentRequest (PENDING_APPROVAL only).
    """
    serializer = ApprovalRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    comment = serializer.validated_data.get("comment")

    try:
        payment_request = services.approve_request(
            requestId,
            request.user.id,
            comment,
            idempotency_key=getattr(request, "idempotency_key", None),
        )
        detail_serializer = PaymentRequestDetailSerializer(payment_request)
        return Response({"data": detail_serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except IntegrityError:
        return Response(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": "Approval conflict (duplicate approval or idempotency)",
                    "details": {},
                }
            },
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST"])
@permission_classes([IsApprover])
def reject_request(request, requestId):
    """
    POST /api/v1/requests/{requestId}/reject

    Reject a PaymentRequest (PENDING_APPROVAL only).
    """
    serializer = ApprovalRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    comment = serializer.validated_data.get("comment")

    try:
        payment_request = services.reject_request(
            requestId,
            request.user.id,
            comment,
            idempotency_key=getattr(request, "idempotency_key", None),
        )
        detail_serializer = PaymentRequestDetailSerializer(payment_request)
        return Response({"data": detail_serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except IntegrityError:
        return Response(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": "Rejection conflict",
                    "details": {},
                }
            },
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST"])
@permission_classes([IsCreatorOrApprover])
def mark_paid(request, requestId):
    """
    POST /api/v1/requests/{requestId}/mark-paid

    Mark a PaymentRequest as PAID (APPROVED only).
    """
    try:
        payment_request = services.mark_paid(
            requestId,
            request.user.id,
            idempotency_key=getattr(request, "idempotency_key", None),
        )
        detail_serializer = PaymentRequestDetailSerializer(payment_request)
        return Response({"data": detail_serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except IntegrityError:
        return Response(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": "Mark-paid conflict (e.g. idempotency)",
                    "details": {},
                }
            },
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST", "GET"])
def upload_or_list_soa(request, batchId, requestId):
    """
    POST /api/v1/batches/{batchId}/requests/{requestId}/soa - Upload SOA
    GET /api/v1/batches/{batchId}/requests/{requestId}/soa - List SOA versions
    """
    if request.method == "POST":
        # Check permission for POST
        if not IsCreator().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if "file" not in request.FILES:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "File is required",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file = request.FILES["file"]

        try:
            soa_version = services.upload_soa(batchId, requestId, request.user.id, file)
            serializer = SOAVersionSerializer(soa_version)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
        except DomainError:
            raise
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "SOA upload conflict",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

    else:  # GET
        # Check permission for GET
        if not IsAuthenticatedReadOnly().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            payment_request = PaymentRequest.objects.get(id=requestId, batch_id=batchId)
        except PaymentRequest.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"PaymentRequest {requestId} does not exist",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        soa_versions = payment_request.soa_versions.all().order_by("version_number")
        serializer = SOAVersionSerializer(soa_versions, many=True)

        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def get_soa_document(request, batchId, requestId, versionId):
    """
    GET /api/v1/batches/{batchId}/requests/{requestId}/soa/{versionId}

    Get SOA version detail with download URL.
    """
    try:
        soa_version = SOAVersion.objects.select_related("payment_request").get(
            id=versionId,
            payment_request_id=requestId,
            payment_request__batch_id=batchId,
        )
    except SOAVersion.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"SOAVersion {versionId} does not exist",
                    "details": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = SOAVersionDetailSerializer(soa_version)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def download_soa_document(request, batchId, requestId, versionId):
    """
    GET /api/v1/batches/{batchId}/requests/{requestId}/soa/{versionId}/download

    Download SOA document file.
    """
    try:
        soa_version = SOAVersion.objects.select_related("payment_request").get(
            id=versionId,
            payment_request_id=requestId,
            payment_request__batch_id=batchId,
        )
    except SOAVersion.DoesNotExist:
        raise Http404("SOA version not found")

    try:
        file = default_storage.open(soa_version.document_reference, "rb")
        from apps.audit.services import create_audit_entry

        create_audit_entry(
            event_type="SOA_DOWNLOADED",
            actor_id=request.user.id if request.user.is_authenticated else None,
            entity_type="SOAVersion",
            entity_id=soa_version.id,
            previous_state=None,
            new_state={
                "version_number": soa_version.version_number,
                "source": soa_version.source,
            },
        )
        return FileResponse(
            file, as_attachment=True, filename=f"soa_v{soa_version.version_number}.pdf"
        )
    except OSError:
        raise Http404("File not found")


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def export_batch_soa(request, batchId):
    """
    GET /api/v1/batches/{batchId}/soa-export?format=pdf|excel

    Export batch SOA as PDF or Excel (immutable snapshot).
    Phase 3: SOA versioned export.
    """
    format_param = request.query_params.get("format", "pdf").lower()
    if format_param not in ("pdf", "excel"):
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Format must be 'pdf' or 'excel'",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        PaymentBatch.objects.get(id=batchId)
    except PaymentBatch.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"PaymentBatch {batchId} does not exist",
                    "details": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    from apps.payments.soa_export import export_batch_soa_pdf, export_batch_soa_excel

    try:
        if format_param == "pdf":
            content, filename = export_batch_soa_pdf(batchId)
            content_type = "application/pdf"
        else:
            content, filename = export_batch_soa_excel(batchId)
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except PaymentBatch.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Batch not found",
                    "details": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )
