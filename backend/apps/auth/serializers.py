"""
Serializers for authentication endpoints.
"""

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Serializer for login request."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("Username and password are required")

        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response."""

    token = serializers.CharField()
    user = serializers.DictField()


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout response."""

    success = serializers.BooleanField(default=True)
