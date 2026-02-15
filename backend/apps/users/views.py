"""
User views: get current user, list users.

No mutations - read-only.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from core.permissions import IsAuthenticatedReadOnly
from apps.users.models import User
from apps.users.serializers import UserSerializer, UserListSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def get_current_user(request):
    """
    GET /api/v1/users/me

    Get current authenticated user.
    """
    serializer = UserSerializer(request.user)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def list_users(request):
    """
    GET /api/v1/users

    List all users with pagination.
    """
    paginator = LimitOffsetPagination()
    paginator.default_limit = 50
    paginator.max_limit = 100

    users = User.objects.all().order_by("username")
    page = paginator.paginate_queryset(users, request)

    serializer = UserListSerializer(page, many=True)

    return paginator.get_paginated_response(serializer.data)
