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
