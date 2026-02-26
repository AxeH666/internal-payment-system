"""
Basic coverage tests for apps.ledger.services.

Directly exercises service functions to hit branches and lines.
"""

import uuid
from django.test import TestCase
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
        username=f"admin_svc_{uuid.uuid4().hex[:8]}",
        password="testpass123",
        display_name="Admin",
        role="ADMIN",
    )


class LedgerServiceTests(TestCase):
    def test_create_client_service(self):
        admin = _admin_user()
        client = ledger_services.create_client(admin.id, "Service Client")
        self.assertEqual(client.name, "Service Client")
        self.assertTrue(client.is_active)

    def test_update_client_service(self):
        admin = _admin_user()
        client = Client.objects.create(name="Before", is_active=True)
        updated = ledger_services.update_client(admin.id, client.id, is_active=False)
        self.assertFalse(updated.is_active)

    def test_create_site_service(self):
        admin = _admin_user()
        client = Client.objects.create(name="Site Client", is_active=True)
        site = ledger_services.create_site(admin.id, "S01", "Site One", client.id)
        self.assertEqual(site.code, "S01")
        self.assertEqual(site.name, "Site One")

    def test_update_site_service(self):
        admin = _admin_user()
        c = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(code="S2", name="Two", client=c, is_active=True)
        updated = ledger_services.update_site(admin.id, site.id, is_active=False)
        self.assertFalse(updated.is_active)

    def test_create_vendor_type_service(self):
        admin = _admin_user()
        vt = ledger_services.create_vendor_type(admin.id, "Type A")
        self.assertEqual(vt.name, "Type A")

    def test_create_subcontractor_scope_service(self):
        admin = _admin_user()
        scope = ledger_services.create_subcontractor_scope(admin.id, "Scope X")
        self.assertEqual(scope.name, "Scope X")

    def test_create_vendor_service(self):
        admin = _admin_user()
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = ledger_services.create_vendor(admin.id, "Vendor One", vt.id)
        self.assertEqual(vendor.name, "Vendor One")

    def test_update_vendor_service(self):
        admin = _admin_user()
        vt = VendorType.objects.create(name="VT2", is_active=True)
        vendor = Vendor.objects.create(name="V", vendor_type=vt, is_active=True)
        updated = ledger_services.update_vendor(admin.id, vendor.id, is_active=False)
        self.assertFalse(updated.is_active)

    def test_create_subcontractor_service(self):
        admin = _admin_user()
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = ledger_services.create_subcontractor(
            admin.id, "Sub One", scope.id, assigned_site_id=None
        )
        self.assertEqual(sub.name, "Sub One")

    def test_update_subcontractor_service(self):
        admin = _admin_user()
        scope = SubcontractorScope.objects.create(name="Sc", is_active=True)
        sub = Subcontractor.objects.create(name="S", scope=scope, is_active=True)
        updated = ledger_services.update_subcontractor(
            admin.id, sub.id, is_active=False
        )
        self.assertFalse(updated.is_active)
