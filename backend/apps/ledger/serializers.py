"""
Ledger serializers - no business logic, validation only.
"""

from rest_framework import serializers
from apps.ledger.models import (
    Client,
    Site,
    VendorType,
    SubcontractorScope,
    Vendor,
    Subcontractor,
)


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    isActive = serializers.BooleanField(source="is_active", default=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Client
        fields = ["id", "name", "isActive", "createdAt"]


class VendorTypeSerializer(serializers.ModelSerializer):
    """Serializer for VendorType."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    isActive = serializers.BooleanField(source="is_active", default=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = VendorType
        fields = ["id", "name", "isActive", "createdAt"]


class SubcontractorScopeSerializer(serializers.ModelSerializer):
    """Serializer for SubcontractorScope."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    isActive = serializers.BooleanField(source="is_active", default=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = SubcontractorScope
        fields = ["id", "name", "isActive", "createdAt"]


class SiteSerializer(serializers.ModelSerializer):
    """Serializer for Site."""

    id = serializers.UUIDField(read_only=True)
    code = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    clientId = serializers.UUIDField(source="client_id", write_only=True)
    client = serializers.StringRelatedField(read_only=True)
    isActive = serializers.BooleanField(source="is_active", default=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Site
        fields = ["id", "code", "name", "clientId", "client", "isActive", "createdAt"]


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    vendorTypeId = serializers.UUIDField(source="vendor_type_id", write_only=True)
    vendorType = serializers.StringRelatedField(read_only=True)
    isActive = serializers.BooleanField(source="is_active", default=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Vendor
        fields = ["id", "name", "vendorTypeId", "vendorType", "isActive", "createdAt"]


class SubcontractorSerializer(serializers.ModelSerializer):
    """Serializer for Subcontractor."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    scopeId = serializers.UUIDField(source="scope_id", write_only=True)
    scope = serializers.StringRelatedField(read_only=True)
    assignedSiteId = serializers.UUIDField(
        source="assigned_site_id", required=False, allow_null=True
    )
    assignedSite = serializers.StringRelatedField(read_only=True)
    isActive = serializers.BooleanField(source="is_active", default=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Subcontractor
        fields = [
            "id",
            "name",
            "scopeId",
            "scope",
            "assignedSiteId",
            "assignedSite",
            "isActive",
            "createdAt",
        ]
