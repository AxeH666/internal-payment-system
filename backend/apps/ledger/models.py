"""
Ledger master data models.

All models follow enterprise hardening:
- is_active pattern (no hard deletes)
- Unique constraints on identifiers
- PROTECT foreign keys
- Temporal tracking (effective_from, deactivated_at)
"""

import uuid
from django.db import models
from django.utils import timezone


class Client(models.Model):
    """Client master data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_clients"
        indexes = [
            models.Index(fields=["is_active"], name="idx_client_active"),
        ]

    def __str__(self):
        return self.name


class Site(models.Model):
    """Site master data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="sites")
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_sites"
        indexes = [
            models.Index(fields=["is_active"], name="idx_site_active"),
            models.Index(fields=["client"], name="idx_site_client"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class VendorType(models.Model):
    """Vendor type master data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_vendor_types"
        indexes = [
            models.Index(fields=["is_active"], name="idx_vendor_type_active"),
        ]

    def __str__(self):
        return self.name


class SubcontractorScope(models.Model):
    """Subcontractor scope master data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_subcontractor_scopes"
        indexes = [
            models.Index(fields=["is_active"], name="idx_scope_active"),
        ]

    def __str__(self):
        return self.name


class Vendor(models.Model):
    """Vendor master data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    vendor_type = models.ForeignKey(
        VendorType, on_delete=models.PROTECT, related_name="vendors"
    )
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_vendors"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "vendor_type"],
                name="unique_vendor_name_per_type",
            )
        ]
        indexes = [
            models.Index(
                fields=["id"],
                condition=models.Q(is_active=True),
                name="idx_vendor_active",
            ),
            models.Index(fields=["vendor_type"], name="idx_vendor_type"),
        ]

    def __str__(self):
        return f"{self.name} ({self.vendor_type.name})"


class Subcontractor(models.Model):
    """Subcontractor master data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    scope = models.ForeignKey(
        SubcontractorScope, on_delete=models.PROTECT, related_name="subcontractors"
    )
    assigned_site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name="assigned_subcontractors",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_subcontractors"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "scope"], name="unique_subcontractor_name_per_scope"
            )
        ]
        indexes = [
            models.Index(fields=["scope"], name="idx_subcontractor_scope"),
            models.Index(fields=["assigned_site"], name="idx_subcontractor_site"),
        ]

    def __str__(self):
        return f"{self.name} ({self.scope.name})"
