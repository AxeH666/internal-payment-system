"""
Ledger services - all mutations flow through this layer.

Rules:
- All mutations wrapped in transaction.atomic
- Use select_for_update for row-level locking
- Create audit entries for all mutations
- No direct model.save() from views
- Admin-only mutations
"""

from django.db import transaction
from django.utils import timezone
from core.exceptions import (
    ValidationError,
    NotFoundError,
    PermissionDeniedError,
)
from apps.ledger.models import (
    Client,
    Site,
    VendorType,
    SubcontractorScope,
    Vendor,
    Subcontractor,
)
from apps.audit.services import create_audit_entry


def create_client(admin_id, name):
    """Create a new Client."""
    from apps.users.models import User, Role

    if not name or not name.strip():
        raise ValidationError("Name must be non-empty")

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can create clients")

    with transaction.atomic():
        client = Client.objects.create(name=name.strip(), is_active=True)

        create_audit_entry(
            event_type="LEDGER_CLIENT_CREATED",
            actor_id=admin_id,
            entity_type="Client",
            entity_id=client.id,
            previous_state=None,
            new_state={"name": client.name, "is_active": True},
        )

        return client


def update_client(admin_id, client_id, is_active=None):
    """Update a Client (only is_active toggle allowed)."""
    from apps.users.models import User, Role

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can update clients")

    try:
        client = Client.objects.select_for_update().get(id=client_id)
    except Client.DoesNotExist:
        raise NotFoundError(f"Client {client_id} does not exist")

    previous_state = {"is_active": client.is_active}

    with transaction.atomic():
        if is_active is not None:
            client.is_active = is_active
            if not is_active:
                client.deactivated_at = timezone.now()
            else:
                client.deactivated_at = None
            client.save()

        create_audit_entry(
            event_type="LEDGER_CLIENT_UPDATED",
            actor_id=admin_id,
            entity_type="Client",
            entity_id=client.id,
            previous_state=previous_state,
            new_state={"is_active": client.is_active},
        )

        return client


def create_vendor_type(admin_id, name):
    """Create a new VendorType."""
    from apps.users.models import User, Role

    if not name or not name.strip():
        raise ValidationError("Name must be non-empty")

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can create vendor types")

    with transaction.atomic():
        vendor_type = VendorType.objects.create(name=name.strip(), is_active=True)

        create_audit_entry(
            event_type="LEDGER_VENDOR_TYPE_CREATED",
            actor_id=admin_id,
            entity_type="VendorType",
            entity_id=vendor_type.id,
            previous_state=None,
            new_state={"name": vendor_type.name, "is_active": True},
        )

        return vendor_type


def create_subcontractor_scope(admin_id, name):
    """Create a new SubcontractorScope."""
    from apps.users.models import User, Role

    if not name or not name.strip():
        raise ValidationError("Name must be non-empty")

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can create subcontractor scopes")

    with transaction.atomic():
        scope = SubcontractorScope.objects.create(name=name.strip(), is_active=True)

        create_audit_entry(
            event_type="LEDGER_SCOPE_CREATED",
            actor_id=admin_id,
            entity_type="SubcontractorScope",
            entity_id=scope.id,
            previous_state=None,
            new_state={"name": scope.name, "is_active": True},
        )

        return scope


def create_site(admin_id, code, name, client_id):
    """Create a new Site."""
    from apps.users.models import User, Role

    if not code or not code.strip():
        raise ValidationError("Code must be non-empty")
    if not name or not name.strip():
        raise ValidationError("Name must be non-empty")

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can create sites")

    try:
        client = Client.objects.get(id=client_id, is_active=True)
    except Client.DoesNotExist:
        raise NotFoundError(f"Active Client {client_id} does not exist")

    with transaction.atomic():
        site = Site.objects.create(
            code=code.strip(),
            name=name.strip(),
            client=client,
            is_active=True,
        )

        create_audit_entry(
            event_type="LEDGER_SITE_CREATED",
            actor_id=admin_id,
            entity_type="Site",
            entity_id=site.id,
            previous_state=None,
            new_state={
                "code": site.code,
                "name": site.name,
                "client_id": str(client_id),
                "is_active": True,
            },
        )

        return site


def update_site(admin_id, site_id, is_active=None):
    """Update a Site (only is_active toggle allowed)."""
    from apps.users.models import User, Role

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can update sites")

    try:
        site = Site.objects.select_for_update().get(id=site_id)
    except Site.DoesNotExist:
        raise NotFoundError(f"Site {site_id} does not exist")

    previous_state = {"is_active": site.is_active}

    with transaction.atomic():
        if is_active is not None:
            site.is_active = is_active
            if not is_active:
                site.deactivated_at = timezone.now()
            else:
                site.deactivated_at = None
            site.save()

        create_audit_entry(
            event_type="LEDGER_SITE_UPDATED",
            actor_id=admin_id,
            entity_type="Site",
            entity_id=site.id,
            previous_state=previous_state,
            new_state={"is_active": site.is_active},
        )

        return site


def create_vendor(admin_id, name, vendor_type_id):
    """Create a new Vendor."""
    from apps.users.models import User, Role

    if not name or not name.strip():
        raise ValidationError("Name must be non-empty")

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can create vendors")

    try:
        vendor_type = VendorType.objects.get(id=vendor_type_id, is_active=True)
    except VendorType.DoesNotExist:
        raise NotFoundError(f"Active VendorType {vendor_type_id} does not exist")

    with transaction.atomic():
        vendor = Vendor.objects.create(
            name=name.strip(),
            vendor_type=vendor_type,
            is_active=True,
        )

        create_audit_entry(
            event_type="LEDGER_VENDOR_CREATED",
            actor_id=admin_id,
            entity_type="Vendor",
            entity_id=vendor.id,
            previous_state=None,
            new_state={
                "name": vendor.name,
                "vendor_type_id": str(vendor_type_id),
                "is_active": True,
            },
        )

        return vendor


def update_vendor(admin_id, vendor_id, is_active=None):
    """Update a Vendor (only is_active toggle allowed)."""
    from apps.users.models import User, Role

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can update vendors")

    try:
        vendor = Vendor.objects.select_for_update().get(id=vendor_id)
    except Vendor.DoesNotExist:
        raise NotFoundError(f"Vendor {vendor_id} does not exist")

    previous_state = {"is_active": vendor.is_active}

    with transaction.atomic():
        if is_active is not None:
            vendor.is_active = is_active
            if not is_active:
                vendor.deactivated_at = timezone.now()
            else:
                vendor.deactivated_at = None
            vendor.save()

        create_audit_entry(
            event_type="LEDGER_VENDOR_UPDATED",
            actor_id=admin_id,
            entity_type="Vendor",
            entity_id=vendor.id,
            previous_state=previous_state,
            new_state={"is_active": vendor.is_active},
        )

        return vendor


def create_subcontractor(admin_id, name, scope_id, assigned_site_id=None):
    """Create a new Subcontractor."""
    from apps.users.models import User, Role

    if not name or not name.strip():
        raise ValidationError("Name must be non-empty")

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can create subcontractors")

    try:
        scope = SubcontractorScope.objects.get(id=scope_id, is_active=True)
    except SubcontractorScope.DoesNotExist:
        raise NotFoundError(f"Active SubcontractorScope {scope_id} does not exist")

    assigned_site = None
    if assigned_site_id:
        try:
            assigned_site = Site.objects.get(id=assigned_site_id, is_active=True)
        except Site.DoesNotExist:
            raise NotFoundError(f"Active Site {assigned_site_id} does not exist")

    with transaction.atomic():
        subcontractor = Subcontractor.objects.create(
            name=name.strip(),
            scope=scope,
            assigned_site=assigned_site,
            is_active=True,
        )

        create_audit_entry(
            event_type="LEDGER_SUBCONTRACTOR_CREATED",
            actor_id=admin_id,
            entity_type="Subcontractor",
            entity_id=subcontractor.id,
            previous_state=None,
            new_state={
                "name": subcontractor.name,
                "scope_id": str(scope_id),
                "assigned_site_id": str(assigned_site_id) if assigned_site_id else None,
                "is_active": True,
            },
        )

        return subcontractor


def update_subcontractor(admin_id, subcontractor_id, is_active=None):
    """Update a Subcontractor (only is_active toggle allowed)."""
    from apps.users.models import User, Role

    try:
        admin = User.objects.get(id=admin_id)
    except User.DoesNotExist:
        raise NotFoundError(f"User {admin_id} does not exist")

    if admin.role != Role.ADMIN:
        raise PermissionDeniedError("Only ADMIN can update subcontractors")

    try:
        subcontractor = Subcontractor.objects.select_for_update().get(
            id=subcontractor_id
        )
    except Subcontractor.DoesNotExist:
        raise NotFoundError(f"Subcontractor {subcontractor_id} does not exist")

    previous_state = {"is_active": subcontractor.is_active}

    with transaction.atomic():
        if is_active is not None:
            subcontractor.is_active = is_active
            if not is_active:
                subcontractor.deactivated_at = timezone.now()
            else:
                subcontractor.deactivated_at = None
            subcontractor.save()

        create_audit_entry(
            event_type="LEDGER_SUBCONTRACTOR_UPDATED",
            actor_id=admin_id,
            entity_type="Subcontractor",
            entity_id=subcontractor.id,
            previous_state=previous_state,
            new_state={"is_active": subcontractor.is_active},
        )

        return subcontractor
