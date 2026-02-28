"""
Branch coverage tests for apps.ledger.services.

Goal: Hit validation, not-found, permission, update branches. Real DB; no mocking.
"""

import uuid

from django.test import TestCase

from core.exceptions import ValidationError, NotFoundError, PermissionDeniedError
from apps.ledger import services as ledger_services
from apps.ledger.models import (
    Client,
    Site,
    VendorType,
    SubcontractorScope,
    Vendor,
    Subcontractor,
)
from apps.users.models import User


def _admin_user():
    return User.objects.create_user(
        username="admin_coverage",
        password="testpass123",
        display_name="Admin",
        role="ADMIN",
    )


def _non_admin_user(role="CREATOR"):
    return User.objects.create_user(
        username=f"nonadmin_{role.lower()}_coverage",
        password="testpass123",
        display_name=role,
        role=role,
    )


# --- create_client ---


class CreateClientCoverageTests(TestCase):
    def test_create_client_validation_empty_name(self):
        admin = _admin_user()
        with self.assertRaises(ValidationError) as ctx:
            ledger_services.create_client(admin.id, "")
        self.assertIn("non-empty", str(ctx.exception))

    def test_create_client_validation_whitespace_name(self):
        admin = _admin_user()
        with self.assertRaises(ValidationError):
            ledger_services.create_client(admin.id, "   ")

    def test_create_client_not_found_admin(self):
        fake_id = uuid.uuid4()
        with self.assertRaises(NotFoundError) as ctx:
            ledger_services.create_client(fake_id, "Acme")
        self.assertIn(str(fake_id), str(ctx.exception))

    def test_create_client_permission_denied(self):
        non_admin = _non_admin_user("CREATOR")
        with self.assertRaises(PermissionDeniedError) as ctx:
            ledger_services.create_client(non_admin.id, "Acme")
        self.assertIn("ADMIN", str(ctx.exception))

    def test_create_client_success(self):
        admin = _admin_user()
        client = ledger_services.create_client(admin.id, " Acme Corp ")
        self.assertEqual(client.name, "Acme Corp")
        self.assertTrue(client.is_active)


# --- update_client ---


class UpdateClientCoverageTests(TestCase):
    def test_update_client_not_found_user(self):
        client = Client.objects.create(name="C1", is_active=True)
        with self.assertRaises(NotFoundError):
            ledger_services.update_client(uuid.uuid4(), client.id, is_active=False)

    def test_update_client_permission_denied(self):
        _admin_user()
        client = Client.objects.create(name="C1", is_active=True)
        non_admin = _non_admin_user("VIEWER")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.update_client(non_admin.id, client.id, is_active=False)

    def test_update_client_not_found_client(self):
        admin = _admin_user()
        with self.assertRaises(NotFoundError):
            ledger_services.update_client(admin.id, uuid.uuid4(), is_active=False)

    def test_update_client_deactivate(self):
        admin = _admin_user()
        client = Client.objects.create(name="C1", is_active=True)
        updated = ledger_services.update_client(admin.id, client.id, is_active=False)
        updated.refresh_from_db()
        self.assertFalse(updated.is_active)
        self.assertIsNotNone(updated.deactivated_at)

    def test_update_client_reactivate(self):
        admin = _admin_user()
        client = Client.objects.create(name="C1", is_active=False)
        updated = ledger_services.update_client(admin.id, client.id, is_active=True)
        updated.refresh_from_db()
        self.assertTrue(updated.is_active)
        self.assertIsNone(updated.deactivated_at)

    def test_update_client_is_active_none(self):
        admin = _admin_user()
        client = Client.objects.create(name="C1", is_active=True)
        updated = ledger_services.update_client(admin.id, client.id, is_active=None)
        self.assertEqual(updated.is_active, True)


# --- create_vendor_type ---


class CreateVendorTypeCoverageTests(TestCase):
    def test_create_vendor_type_validation_empty_name(self):
        admin = _admin_user()
        with self.assertRaises(ValidationError):
            ledger_services.create_vendor_type(admin.id, "")

    def test_create_vendor_type_not_found_admin(self):
        with self.assertRaises(NotFoundError):
            ledger_services.create_vendor_type(uuid.uuid4(), "Labour")

    def test_create_vendor_type_permission_denied(self):
        non_admin = _non_admin_user("APPROVER")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.create_vendor_type(non_admin.id, "Labour")

    def test_create_vendor_type_success(self):
        admin = _admin_user()
        vt = ledger_services.create_vendor_type(admin.id, " Labour ")
        self.assertEqual(vt.name, "Labour")
        self.assertTrue(vt.is_active)


# --- create_subcontractor_scope ---


class CreateSubcontractorScopeCoverageTests(TestCase):
    def test_create_scope_validation_empty_name(self):
        admin = _admin_user()
        with self.assertRaises(ValidationError):
            ledger_services.create_subcontractor_scope(admin.id, "")

    def test_create_scope_not_found_admin(self):
        with self.assertRaises(NotFoundError):
            ledger_services.create_subcontractor_scope(uuid.uuid4(), "Electrical")

    def test_create_scope_permission_denied(self):
        non_admin = _non_admin_user("CREATOR")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.create_subcontractor_scope(non_admin.id, "Electrical")

    def test_create_scope_success(self):
        admin = _admin_user()
        scope = ledger_services.create_subcontractor_scope(admin.id, " Electrical ")
        self.assertEqual(scope.name, "Electrical")
        self.assertTrue(scope.is_active)


# --- create_site ---


class CreateSiteCoverageTests(TestCase):
    def test_create_site_validation_empty_code(self):
        admin = _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        with self.assertRaises(ValidationError):
            ledger_services.create_site(admin.id, "", "Site A", client.id)

    def test_create_site_validation_empty_name(self):
        admin = _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        with self.assertRaises(ValidationError):
            ledger_services.create_site(admin.id, "S1", "", client.id)

    def test_create_site_not_found_admin(self):
        client = Client.objects.create(name="C", is_active=True)
        with self.assertRaises(NotFoundError):
            ledger_services.create_site(uuid.uuid4(), "S1", "Site A", client.id)

    def test_create_site_permission_denied(self):
        _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        non_admin = _non_admin_user("VIEWER")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.create_site(non_admin.id, "S1", "Site A", client.id)

    def test_create_site_not_found_client(self):
        admin = _admin_user()
        with self.assertRaises(NotFoundError) as ctx:
            ledger_services.create_site(admin.id, "S1", "Site A", uuid.uuid4())
        self.assertIn("Client", str(ctx.exception))

    def test_create_site_success(self):
        admin = _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        site = ledger_services.create_site(admin.id, " S1 ", " Site A ", client.id)
        self.assertEqual(site.code, "S1")
        self.assertEqual(site.name, "Site A")
        self.assertEqual(site.client_id, client.id)
        self.assertTrue(site.is_active)


# --- update_site ---


class UpdateSiteCoverageTests(TestCase):
    def test_update_site_not_found_user(self):
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="S1", name="Site", client=client, is_active=True
        )
        with self.assertRaises(NotFoundError):
            ledger_services.update_site(uuid.uuid4(), site.id, is_active=False)

    def test_update_site_permission_denied(self):
        _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="S1", name="Site", client=client, is_active=True
        )
        non_admin = _non_admin_user("APPROVER")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.update_site(non_admin.id, site.id, is_active=False)

    def test_update_site_not_found_site(self):
        admin = _admin_user()
        with self.assertRaises(NotFoundError):
            ledger_services.update_site(admin.id, uuid.uuid4(), is_active=False)

    def test_update_site_deactivate(self):
        admin = _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="S1", name="Site", client=client, is_active=True
        )
        updated = ledger_services.update_site(admin.id, site.id, is_active=False)
        updated.refresh_from_db()
        self.assertFalse(updated.is_active)
        self.assertIsNotNone(updated.deactivated_at)

    def test_update_site_reactivate(self):
        admin = _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="S1", name="Site", client=client, is_active=False
        )
        updated = ledger_services.update_site(admin.id, site.id, is_active=True)
        updated.refresh_from_db()
        self.assertTrue(updated.is_active)
        self.assertIsNone(updated.deactivated_at)


# --- create_vendor ---


class CreateVendorCoverageTests(TestCase):
    def test_create_vendor_validation_empty_name(self):
        admin = _admin_user()
        vt = VendorType.objects.create(name="VT", is_active=True)
        with self.assertRaises(ValidationError):
            ledger_services.create_vendor(admin.id, "", vt.id)

    def test_create_vendor_not_found_admin(self):
        vt = VendorType.objects.create(name="VT", is_active=True)
        with self.assertRaises(NotFoundError):
            ledger_services.create_vendor(uuid.uuid4(), "V1", vt.id)

    def test_create_vendor_permission_denied(self):
        _admin_user()
        vt = VendorType.objects.create(name="VT", is_active=True)
        non_admin = _non_admin_user("VIEWER")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.create_vendor(non_admin.id, "V1", vt.id)

    def test_create_vendor_not_found_vendor_type(self):
        admin = _admin_user()
        with self.assertRaises(NotFoundError) as ctx:
            ledger_services.create_vendor(admin.id, "V1", uuid.uuid4())
        self.assertIn("VendorType", str(ctx.exception))

    def test_create_vendor_success(self):
        admin = _admin_user()
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = ledger_services.create_vendor(admin.id, " Vendor One ", vt.id)
        self.assertEqual(vendor.name, "Vendor One")
        self.assertEqual(vendor.vendor_type_id, vt.id)
        self.assertTrue(vendor.is_active)


# --- update_vendor ---


class UpdateVendorCoverageTests(TestCase):
    def test_update_vendor_not_found_user(self):
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = Vendor.objects.create(name="V1", vendor_type=vt, is_active=True)
        with self.assertRaises(NotFoundError):
            ledger_services.update_vendor(uuid.uuid4(), vendor.id, is_active=False)

    def test_update_vendor_permission_denied(self):
        _admin_user()
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = Vendor.objects.create(name="V1", vendor_type=vt, is_active=True)
        non_admin = _non_admin_user("CREATOR")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.update_vendor(non_admin.id, vendor.id, is_active=False)

    def test_update_vendor_not_found_vendor(self):
        admin = _admin_user()
        with self.assertRaises(NotFoundError):
            ledger_services.update_vendor(admin.id, uuid.uuid4(), is_active=False)

    def test_update_vendor_deactivate(self):
        admin = _admin_user()
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = Vendor.objects.create(name="V1", vendor_type=vt, is_active=True)
        updated = ledger_services.update_vendor(admin.id, vendor.id, is_active=False)
        updated.refresh_from_db()
        self.assertFalse(updated.is_active)
        self.assertIsNotNone(updated.deactivated_at)

    def test_update_vendor_reactivate(self):
        admin = _admin_user()
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = Vendor.objects.create(name="V1", vendor_type=vt, is_active=False)
        updated = ledger_services.update_vendor(admin.id, vendor.id, is_active=True)
        updated.refresh_from_db()
        self.assertTrue(updated.is_active)
        self.assertIsNone(updated.deactivated_at)


# --- create_subcontractor ---


class CreateSubcontractorCoverageTests(TestCase):
    def test_create_subcontractor_validation_empty_name(self):
        admin = _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        with self.assertRaises(ValidationError):
            ledger_services.create_subcontractor(admin.id, "", scope.id)

    def test_create_subcontractor_not_found_admin(self):
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        with self.assertRaises(NotFoundError):
            ledger_services.create_subcontractor(uuid.uuid4(), "Sub1", scope.id)

    def test_create_subcontractor_permission_denied(self):
        _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        non_admin = _non_admin_user("APPROVER")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.create_subcontractor(non_admin.id, "Sub1", scope.id)

    def test_create_subcontractor_not_found_scope(self):
        admin = _admin_user()
        with self.assertRaises(NotFoundError) as ctx:
            ledger_services.create_subcontractor(admin.id, "Sub1", uuid.uuid4())
        self.assertIn("SubcontractorScope", str(ctx.exception))

    def test_create_subcontractor_not_found_site_when_assigned(self):
        admin = _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        with self.assertRaises(NotFoundError) as ctx:
            ledger_services.create_subcontractor(
                admin.id, "Sub1", scope.id, assigned_site_id=uuid.uuid4()
            )
        self.assertIn("Site", str(ctx.exception))

    def test_create_subcontractor_success_without_site(self):
        admin = _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = ledger_services.create_subcontractor(admin.id, " Sub One ", scope.id)
        self.assertEqual(sub.name, "Sub One")
        self.assertEqual(sub.scope_id, scope.id)
        self.assertIsNone(sub.assigned_site_id)
        self.assertTrue(sub.is_active)

    def test_create_subcontractor_success_with_site(self):
        admin = _admin_user()
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="SC", name="Site", client=client, is_active=True
        )
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = ledger_services.create_subcontractor(
            admin.id, "Sub1", scope.id, assigned_site_id=site.id
        )
        self.assertEqual(sub.assigned_site_id, site.id)
        self.assertTrue(sub.is_active)


# --- update_subcontractor ---


class UpdateSubcontractorCoverageTests(TestCase):
    def test_update_subcontractor_not_found_user(self):
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = Subcontractor.objects.create(name="Sub1", scope=scope, is_active=True)
        with self.assertRaises(NotFoundError):
            ledger_services.update_subcontractor(uuid.uuid4(), sub.id, is_active=False)

    def test_update_subcontractor_permission_denied(self):
        _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = Subcontractor.objects.create(name="Sub1", scope=scope, is_active=True)
        non_admin = _non_admin_user("VIEWER")
        with self.assertRaises(PermissionDeniedError):
            ledger_services.update_subcontractor(non_admin.id, sub.id, is_active=False)

    def test_update_subcontractor_not_found_subcontractor(self):
        admin = _admin_user()
        with self.assertRaises(NotFoundError):
            ledger_services.update_subcontractor(
                admin.id, uuid.uuid4(), is_active=False
            )

    def test_update_subcontractor_deactivate(self):
        admin = _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = Subcontractor.objects.create(name="Sub1", scope=scope, is_active=True)
        updated = ledger_services.update_subcontractor(
            admin.id, sub.id, is_active=False
        )
        updated.refresh_from_db()
        self.assertFalse(updated.is_active)
        self.assertIsNotNone(updated.deactivated_at)

    def test_update_subcontractor_reactivate(self):
        admin = _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = Subcontractor.objects.create(name="Sub1", scope=scope, is_active=False)
        updated = ledger_services.update_subcontractor(admin.id, sub.id, is_active=True)
        updated.refresh_from_db()
        self.assertTrue(updated.is_active)
        self.assertIsNone(updated.deactivated_at)
