"""
Branch coverage tests for apps.ledger.views.

Goal: Hit HTTP, permission, validation, alternate return paths. APIClient, real DB.
"""

import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
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
        username="admin_views",
        password="testpass123",
        display_name="Admin",
        role="ADMIN",
    )


def _viewer_user():
    return User.objects.create_user(
        username="viewer_views",
        password="testpass123",
        display_name="Viewer",
        role="VIEWER",
    )


def _creator_user():
    return User.objects.create_user(
        username="creator_views",
        password="testpass123",
        display_name="Creator",
        role="CREATOR",
    )


BASE = "/api/v1/ledger"


def _idem_headers():
    """Idempotency-Key required by middleware for POST/PATCH."""
    return {"HTTP_IDEMPOTENCY_KEY": "ledger-views-coverage"}


# -----------------------------
# 1. Unauthorized (no auth)
# -----------------------------


class UnauthorizedAccessTests(TestCase):
    """No auth → 401 (DRF returns Unauthorized for unauthenticated)."""

    def setUp(self):
        self.client = APIClient()

    def test_get_clients_unauthorized_returns_401(self):
        r = self.client.get(f"{BASE}/clients")
        self.assertEqual(r.status_code, 401)

    def test_post_clients_unauthorized_returns_401(self):
        r = self.client.post(
            f"{BASE}/clients",
            {"name": "Acme"},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 401)

    def test_get_sites_unauthorized_returns_401(self):
        r = self.client.get(f"{BASE}/sites")
        self.assertEqual(r.status_code, 401)

    def test_get_vendors_unauthorized_returns_401(self):
        r = self.client.get(f"{BASE}/vendors")
        self.assertEqual(r.status_code, 401)

    def test_get_subcontractors_unauthorized_returns_401(self):
        r = self.client.get(f"{BASE}/subcontractors")
        self.assertEqual(r.status_code, 401)

    def test_get_vendor_types_unauthorized_returns_401(self):
        r = self.client.get(f"{BASE}/vendor-types")
        self.assertEqual(r.status_code, 401)

    def test_get_scopes_unauthorized_returns_401(self):
        r = self.client.get(f"{BASE}/scopes")
        self.assertEqual(r.status_code, 401)


# -----------------------------
# 2. Wrong role (403)
# -----------------------------


class WrongRoleAccessTests(TestCase):
    """Authenticated but wrong role → 403."""

    def setUp(self):
        self.client = APIClient()
        self.viewer = _viewer_user()
        self.creator = _creator_user()

    def test_post_clients_as_viewer_returns_403(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.post(
            f"{BASE}/clients",
            {"name": "Acme"},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 403)
        self.assertIn("error", r.json())
        self.assertEqual(r.json()["error"]["code"], "FORBIDDEN")

    def test_post_sites_as_viewer_returns_403(self):
        self.client.force_authenticate(user=self.viewer)
        client = Client.objects.create(name="C", is_active=True)
        r = self.client.post(
            f"{BASE}/sites",
            {"code": "S1", "name": "Site", "clientId": str(client.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 403)

    def test_post_vendors_as_creator_returns_403(self):
        self.client.force_authenticate(user=self.creator)
        vt = VendorType.objects.create(name="VT", is_active=True)
        r = self.client.post(
            f"{BASE}/vendors",
            {"name": "V1", "vendorTypeId": str(vt.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 403)

    def test_post_subcontractors_as_viewer_returns_403(self):
        self.client.force_authenticate(user=self.viewer)
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        r = self.client.post(
            f"{BASE}/subcontractors",
            {"name": "Sub1", "scopeId": str(scope.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 403)

    def test_patch_client_as_viewer_returns_403(self):
        self.client.force_authenticate(user=self.viewer)
        client = Client.objects.create(name="C", is_active=True)
        r = self.client.patch(
            f"{BASE}/clients/{client.id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 403)


# -----------------------------
# 3. Invalid / not-found ID (404)
# -----------------------------


class NotFoundTests(TestCase):
    """Valid UUID but resource does not exist → 404 (DomainError from service)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_patch_client_not_found_returns_404(self):
        fake_id = uuid.uuid4()
        r = self.client.patch(
            f"{BASE}/clients/{fake_id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.json())

    def test_patch_site_not_found_returns_404(self):
        fake_id = uuid.uuid4()
        r = self.client.patch(
            f"{BASE}/sites/{fake_id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 404)

    def test_patch_vendor_not_found_returns_404(self):
        fake_id = uuid.uuid4()
        r = self.client.patch(
            f"{BASE}/vendors/{fake_id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 404)

    def test_patch_subcontractor_not_found_returns_404(self):
        fake_id = uuid.uuid4()
        r = self.client.patch(
            f"{BASE}/subcontractors/{fake_id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 404)


# -----------------------------
# 4. Invalid payload (400)
# -----------------------------


class ValidationErrorTests(TestCase):
    """Missing or invalid payload → 400."""

    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_post_client_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.post(
            f"{BASE}/clients",
            {},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Name", r.json()["error"]["message"])

    def test_post_client_empty_name_returns_400(self):
        r = self.client.post(
            f"{BASE}/clients",
            {"name": ""},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)

    def test_patch_client_missing_is_active_returns_400(self):
        client = Client.objects.create(name="C", is_active=True)
        r = self.client.patch(
            f"{BASE}/clients/{client.id}",
            {},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("isActive", r.json()["error"]["message"])

    def test_post_site_missing_code_and_name_returns_400(self):
        client = Client.objects.create(name="C", is_active=True)
        r = self.client.post(
            f"{BASE}/sites",
            {"clientId": str(client.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("code", r.json()["error"]["message"].lower())

    def test_post_vendor_missing_name_returns_400(self):
        vt = VendorType.objects.create(name="VT", is_active=True)
        r = self.client.post(
            f"{BASE}/vendors",
            {"vendorTypeId": str(vt.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)

    def test_post_subcontractor_missing_name_and_scope_returns_400(self):
        r = self.client.post(
            f"{BASE}/subcontractors",
            {},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("scopeId", r.json()["error"]["message"])

    def test_patch_site_missing_is_active_returns_400(self):
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="S1", name="Site", client=client, is_active=True
        )
        r = self.client.patch(
            f"{BASE}/sites/{site.id}",
            {},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)

    def test_patch_vendor_missing_is_active_returns_400(self):
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = Vendor.objects.create(name="V1", vendor_type=vt, is_active=True)
        r = self.client.patch(
            f"{BASE}/vendors/{vendor.id}",
            {},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)

    def test_patch_subcontractor_missing_is_active_returns_400(self):
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = Subcontractor.objects.create(name="Sub1", scope=scope, is_active=True)
        r = self.client.patch(
            f"{BASE}/subcontractors/{sub.id}",
            {},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 400)


# -----------------------------
# 5. Successful POST → 201
# -----------------------------


class SuccessfulCreateTests(TestCase):
    """Admin POST → 201 and audit entry."""

    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_post_client_returns_201(self):
        before = AuditLog.objects.count()
        r = self.client.post(
            f"{BASE}/clients",
            {"name": "New Client"},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 201)
        self.assertIn("data", r.json())
        self.assertEqual(r.json()["data"]["name"], "New Client")
        self.assertEqual(AuditLog.objects.count(), before + 1)
        self.assertTrue(
            AuditLog.objects.filter(event_type="LEDGER_CLIENT_CREATED").exists()
        )

    def test_post_site_with_client_id_returns_201(self):
        client = Client.objects.create(name="SiteClient", is_active=True)
        r = self.client.post(
            f"{BASE}/sites",
            {"code": "SC1", "name": "Site One", "clientId": str(client.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["data"]["code"], "SC1")
        self.assertTrue(
            AuditLog.objects.filter(event_type="LEDGER_SITE_CREATED").exists()
        )

    def test_post_site_without_client_id_uses_default_client(self):
        """Branch: no clientId → get_or_create Default Client."""
        r = self.client.post(
            f"{BASE}/sites",
            {"code": "DEF1", "name": "Default Site"},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 201)
        self.assertIn("data", r.json())
        default = Client.objects.filter(name="Default Client").first()
        self.assertIsNotNone(default)

    def test_post_vendor_returns_201(self):
        vt = VendorType.objects.create(name="Labour", is_active=True)
        r = self.client.post(
            f"{BASE}/vendors",
            {"name": "Vendor One", "vendorTypeId": str(vt.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["data"]["name"], "Vendor One")
        self.assertTrue(
            AuditLog.objects.filter(event_type="LEDGER_VENDOR_CREATED").exists()
        )

    def test_post_vendor_without_vendor_type_id_uses_default(self):
        """Branch: no vendorTypeId → get_or_create Default vendor type."""
        r = self.client.post(
            f"{BASE}/vendors",
            {"name": "V No Type"},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 201)
        default = VendorType.objects.filter(name="Default").first()
        self.assertIsNotNone(default)

    def test_post_subcontractor_returns_201(self):
        scope = SubcontractorScope.objects.create(name="Electrical", is_active=True)
        r = self.client.post(
            f"{BASE}/subcontractors",
            {"name": "Sub One", "scopeId": str(scope.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(
            AuditLog.objects.filter(event_type="LEDGER_SUBCONTRACTOR_CREATED").exists()
        )


# -----------------------------
# 6–7. PATCH deactivate / reactivate → 200
# -----------------------------


class PatchUpdateTests(TestCase):
    """PATCH isActive → 200 and audit."""

    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_patch_client_deactivate_returns_200(self):
        client = Client.objects.create(name="DeactClient", is_active=True)
        r = self.client.patch(
            f"{BASE}/clients/{client.id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["data"]["isActive"])
        client.refresh_from_db()
        self.assertFalse(client.is_active)
        self.assertTrue(
            AuditLog.objects.filter(event_type="LEDGER_CLIENT_UPDATED").exists()
        )

    def test_patch_client_reactivate_returns_200(self):
        client = Client.objects.create(name="ReactClient", is_active=False)
        r = self.client.patch(
            f"{BASE}/clients/{client.id}",
            {"isActive": True},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["isActive"])

    def test_patch_site_deactivate_returns_200(self):
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="P1", name="Patch Site", client=client, is_active=True
        )
        r = self.client.patch(
            f"{BASE}/sites/{site.id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["data"]["isActive"])

    def test_patch_site_reactivate_returns_200(self):
        client = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(
            code="P2", name="React Site", client=client, is_active=False
        )
        r = self.client.patch(
            f"{BASE}/sites/{site.id}",
            {"isActive": True},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["isActive"])

    def test_patch_vendor_deactivate_returns_200(self):
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = Vendor.objects.create(name="V Patch", vendor_type=vt, is_active=True)
        r = self.client.patch(
            f"{BASE}/vendors/{vendor.id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["data"]["isActive"])

    def test_patch_vendor_reactivate_returns_200(self):
        vt = VendorType.objects.create(name="VT", is_active=True)
        vendor = Vendor.objects.create(name="V React", vendor_type=vt, is_active=False)
        r = self.client.patch(
            f"{BASE}/vendors/{vendor.id}",
            {"isActive": True},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["isActive"])

    def test_patch_subcontractor_deactivate_returns_200(self):
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = Subcontractor.objects.create(
            name="Sub Patch", scope=scope, is_active=True
        )
        r = self.client.patch(
            f"{BASE}/subcontractors/{sub.id}",
            {"isActive": False},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["data"]["isActive"])

    def test_patch_subcontractor_reactivate_returns_200(self):
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        sub = Subcontractor.objects.create(
            name="Sub React", scope=scope, is_active=False
        )
        r = self.client.patch(
            f"{BASE}/subcontractors/{sub.id}",
            {"isActive": True},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["isActive"])


# -----------------------------
# 8. Invalid HTTP method → 405
# -----------------------------


class MethodNotAllowedTests(TestCase):
    """Wrong HTTP method → 405."""

    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.viewer = _viewer_user()
        self.client.force_authenticate(user=self.admin)

    def test_put_clients_returns_405(self):
        r = self.client.put(
            f"{BASE}/clients",
            {"name": "Acme"},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 405)

    def test_patch_clients_list_returns_405(self):
        r = self.client.patch(
            f"{BASE}/clients",
            {},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 405)

    def test_delete_client_returns_405(self):
        client = Client.objects.create(name="C", is_active=True)
        r = self.client.delete(f"{BASE}/clients/{client.id}")
        self.assertEqual(r.status_code, 405)

    def test_post_vendor_types_returns_405_or_403(self):
        """POST to read-only endpoint: 405 or 403."""
        self.client.force_authenticate(user=self.admin)
        r = self.client.post(
            f"{BASE}/vendor-types",
            {"name": "X"},
            format="json",
            **_idem_headers(),
        )
        self.assertIn(r.status_code, (403, 405))

    def test_post_scopes_returns_405_or_403(self):
        """POST to read-only endpoint: 405 or 403."""
        r = self.client.post(
            f"{BASE}/scopes",
            {"name": "X"},
            format="json",
            **_idem_headers(),
        )
        self.assertIn(r.status_code, (403, 405))

    def test_get_update_client_returns_405(self):
        client = Client.objects.create(name="C", is_active=True)
        r = self.client.get(f"{BASE}/clients/{client.id}")
        self.assertEqual(r.status_code, 405)


# -----------------------------
# 9. GET list (authenticated, correct role) → 200
# -----------------------------


class ListEndpointsTests(TestCase):
    """GET list with auth → 200 and data shape."""

    def setUp(self):
        self.client = APIClient()
        self.viewer = _viewer_user()
        self.admin = _admin_user()

    def test_get_clients_returns_200_and_data(self):
        self.client.force_authenticate(user=self.viewer)
        Client.objects.create(name="A", is_active=True)
        r = self.client.get(f"{BASE}/clients")
        self.assertEqual(r.status_code, 200)
        self.assertIn("data", r.json())
        self.assertIsInstance(r.json()["data"], list)

    def test_get_sites_returns_200_and_data(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.get(f"{BASE}/sites")
        self.assertEqual(r.status_code, 200)
        self.assertIn("data", r.json())

    def test_get_vendors_returns_200_and_data(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.get(f"{BASE}/vendors")
        self.assertEqual(r.status_code, 200)
        self.assertIn("data", r.json())

    def test_get_subcontractors_returns_200_and_data(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.get(f"{BASE}/subcontractors")
        self.assertEqual(r.status_code, 200)
        self.assertIn("data", r.json())

    def test_get_vendor_types_returns_200_and_data(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.get(f"{BASE}/vendor-types")
        self.assertEqual(r.status_code, 200)
        self.assertIn("data", r.json())

    def test_get_scopes_returns_200_and_data(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.get(f"{BASE}/scopes")
        self.assertEqual(r.status_code, 200)
        self.assertIn("data", r.json())

    def test_get_clients_empty_list_returns_200(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.get(f"{BASE}/clients")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"], [])


# -----------------------------
# 10. Conflict (409) branches where applicable
# -----------------------------


class ConflictTests(TestCase):
    """Duplicate name/code → 409 (IntegrityError in view)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_post_client_duplicate_name_returns_409(self):
        Client.objects.create(name="Duplicate", is_active=True)
        r = self.client.post(
            f"{BASE}/clients",
            {"name": "Duplicate"},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "CONFLICT")
        self.assertIn("already exists", r.json()["error"]["message"])

    def test_post_site_duplicate_code_returns_409(self):
        client = Client.objects.create(name="C", is_active=True)
        Site.objects.create(code="DUP", name="First", client=client, is_active=True)
        r = self.client.post(
            f"{BASE}/sites",
            {"code": "DUP", "name": "Second", "clientId": str(client.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 409)
        self.assertIn("already exists", r.json()["error"]["message"])

    def test_post_vendor_duplicate_name_per_type_returns_409(self):
        vt = VendorType.objects.create(name="VT", is_active=True)
        Vendor.objects.create(name="SameName", vendor_type=vt, is_active=True)
        r = self.client.post(
            f"{BASE}/vendors",
            {"name": "SameName", "vendorTypeId": str(vt.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 409)
        self.assertIn("already exists", r.json()["error"]["message"])

    def test_post_subcontractor_duplicate_name_per_scope_returns_409(self):
        scope = SubcontractorScope.objects.create(name="Scope", is_active=True)
        Subcontractor.objects.create(name="SameSub", scope=scope, is_active=True)
        r = self.client.post(
            f"{BASE}/subcontractors",
            {"name": "SameSub", "scopeId": str(scope.id)},
            format="json",
            **_idem_headers(),
        )
        self.assertEqual(r.status_code, 409)
        self.assertIn("already exists", r.json()["error"]["message"])
