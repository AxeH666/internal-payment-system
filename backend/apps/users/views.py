"""
User views: get current user, list users, create users.

User creation requires ADMIN role.
"""

from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from core.permissions import IsAuthenticatedReadOnly, IsAdmin
from apps.users.models import User
from apps.users.serializers import (
    UserSerializer,
    UserListSerializer,
    UserCreateSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def get_current_user(request):
    """
    GET /api/v1/users/me

    Get current authenticated user.
    """
    serializer = UserSerializer(request.user)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
def list_or_create_users(request):
    """
    GET /api/v1/users - List all users with pagination (authenticated users).
    POST /api/v1/users - Create a new user (ADMIN only).
    """
    if request.method == "GET":
        # GET requires authenticated user (any role)
        if not IsAuthenticatedReadOnly().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required",
                        "details": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        paginator = LimitOffsetPagination()
        paginator.default_limit = 50
        paginator.max_limit = 100

        users = User.objects.all().order_by("username")
        page = paginator.paginate_queryset(users, request)

        serializer = UserListSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    else:  # POST
        # POST requires ADMIN permission
        if not IsAdmin().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Only ADMIN can create users",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        display_name = serializer.validated_data.get("display_name") or username
        role = serializer.validated_data["role"]

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                display_name=display_name,
                role=role,
            )
            response_serializer = UserSerializer(user)
            return Response(
                {"data": response_serializer.data}, status=status.HTTP_201_CREATED
            )
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": f"User with username '{username}' already exists",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
