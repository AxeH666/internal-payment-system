"""
Audit log views - query audit log entries.

Read-only - audit logs are append-only.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.utils.dateparse import parse_datetime
from core.permissions import IsAuthenticatedReadOnly
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def query_audit_log(request):
    """
    GET /api/v1/audit

    Query audit log entries with optional filters.
    """
    entity_type = request.query_params.get("entityType")
    entity_id = request.query_params.get("entityId")
    actor_id = request.query_params.get("actorId")
    from_date = request.query_params.get("fromDate")
    to_date = request.query_params.get("toDate")

    queryset = AuditLog.objects.all()

    # Apply filters
    if entity_type:
        if entity_type not in ["PaymentBatch", "PaymentRequest"]:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid entityType",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.filter(entity_type=entity_type)

    if entity_id:
        try:
            from uuid import UUID

            queryset = queryset.filter(entity_id=UUID(entity_id))
        except ValueError:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid entityId format",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    if actor_id:
        try:
            from uuid import UUID

            queryset = queryset.filter(actor_id=UUID(actor_id))
        except ValueError:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid actorId format",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    if from_date:
        try:
            from_dt = parse_datetime(from_date)
            if from_dt:
                queryset = queryset.filter(occurred_at__gte=from_dt)
            else:
                return Response(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid fromDate format (use ISO 8601)",
                            "details": {},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid fromDate format",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    if to_date:
        try:
            to_dt = parse_datetime(to_date)
            if to_dt:
                queryset = queryset.filter(occurred_at__lte=to_dt)
            else:
                return Response(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid toDate format (use ISO 8601)",
                            "details": {},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid toDate format",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Order by occurred_at descending
    queryset = queryset.order_by("-occurred_at")

    # Paginate
    paginator = LimitOffsetPagination()
    paginator.default_limit = 50
    paginator.max_limit = 100

    page = paginator.paginate_queryset(queryset, request)
    serializer = AuditLogSerializer(page, many=True)

    return paginator.get_paginated_response(serializer.data)
