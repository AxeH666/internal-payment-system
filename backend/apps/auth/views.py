"""
Authentication views: login, logout.

No domain logic - authentication only.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from apps.auth.serializers import LoginSerializer
from apps.users.serializers import UserSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/v1/auth/login

    Authenticate user and return JWT token.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid credentials",
                    "details": {},
                }
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Generate tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Serialize user
    user_data = UserSerializer(user).data

    return Response(
        {"data": {"token": access_token, "user": user_data}}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([])  # Requires authentication via JWT
def logout(request):
    """
    POST /api/v1/auth/logout

    Logout user and invalidate refresh token.
    """
    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        # Token may already be invalid, ignore
        pass

    return Response({"data": {"success": True}}, status=status.HTTP_200_OK)
