"""
Serializers for User model.

No business logic in serializers - validation only.
"""

from rest_framework import serializers
from apps.users.models import User, Role


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    id = serializers.UUIDField(read_only=True)
    role = serializers.ChoiceField(choices=Role.choices, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "displayName", "role"]
        read_only_fields = ["id", "role"]

    displayName = serializers.CharField(source="display_name", read_only=True)


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list endpoint."""

    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "displayName", "role"]

    displayName = serializers.CharField(source="display_name", read_only=True)


class UserCreateSerializer(serializers.Serializer):
    """Serializer for user creation endpoint."""

    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(write_only=True, required=True)
    displayName = serializers.CharField(
        max_length=255, required=False, source="display_name"
    )
    role = serializers.ChoiceField(choices=Role.choices, required=True)

    def validate_role(self, value):
        """Ensure only CREATOR, APPROVER, or VIEWER can be created (not ADMIN)."""
        if value == Role.ADMIN:
            raise serializers.ValidationError("Cannot create ADMIN users via API")
        return value
