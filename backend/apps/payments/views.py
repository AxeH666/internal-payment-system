"""
Payment API views.

All mutations flow through service layer.
All endpoints define permission_classes per API contract.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage

from core.permissions import (
    IsCreator,
    IsApprover,
    IsCreatorOrApprover,
    IsAuthenticatedReadOnly,
)
from core.exceptions import DomainError
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

        title = request.data.get("title")

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
        except Exception:
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An error occurred",
                        "details": {},
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        batch = PaymentBatch.objects.prefetch_related("requests").get(id=batchId)
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
    except Exception:
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    except Exception:
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsCreator])
def add_request(request, batchId):
    """
    POST /api/v1/batches/{batchId}/requests

    Add a PaymentRequest to a PaymentBatch.
    """
    amount = request.data.get("amount")
    currency = request.data.get("currency")
    beneficiary_name = request.data.get("beneficiaryName")
    beneficiary_account = request.data.get("beneficiaryAccount")
    purpose = request.data.get("purpose")

    # Convert amount string to decimal
    try:
        from decimal import Decimal

        amount = Decimal(str(amount)) if amount else None
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

    try:
        payment_request = services.add_request(
            batchId,
            request.user.id,
            amount,
            currency,
            beneficiary_name,
            beneficiary_account,
            purpose,
        )
        serializer = PaymentRequestSerializer(payment_request)
        return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
    except DomainError:
        raise
    except Exception:
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        except DomainError:
            raise
        except Exception:
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An error occurred",
                        "details": {},
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
        payment_request = services.approve_request(requestId, request.user.id, comment)
        detail_serializer = PaymentRequestDetailSerializer(payment_request)
        return Response({"data": detail_serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except Exception:
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        payment_request = services.reject_request(requestId, request.user.id, comment)
        detail_serializer = PaymentRequestDetailSerializer(payment_request)
        return Response({"data": detail_serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except Exception:
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsCreatorOrApprover])
def mark_paid(request, requestId):
    """
    POST /api/v1/requests/{requestId}/mark-paid

    Mark a PaymentRequest as PAID (APPROVED only).
    """
    try:
        payment_request = services.mark_paid(requestId, request.user.id)
        detail_serializer = PaymentRequestDetailSerializer(payment_request)
        return Response({"data": detail_serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise
    except Exception:
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        except Exception:
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An error occurred",
                        "details": {},
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        return FileResponse(
            file, as_attachment=True, filename=f"soa_v{soa_version.version_number}.pdf"
        )
    except Exception:
        raise Http404("File not found")
