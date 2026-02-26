"""
Basic API coverage tests for apps.ledger.views.

Covers list/create endpoints, permission denial, validation errors, and update (PATCH).
"""

import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from apps.ledger.models import Client, Site


def _idem_headers():
    return {"HTTP_IDEMPOTENCY_KEY": "ledger-basic-" + uuid.uuid4().hex[:8]}


class LedgerViewBasicTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=f"user_{uuid.uuid4().hex[:8]}",
            password="testpass123",
            display_name="Test User",
            role="ADMIN",
        )
        self.client.force_authenticate(self.user)

    def test_client_create_success(self):
        url = reverse("ledger:list-or-create-clients")
        data = {"name": "Test Client"}
        response = self.client.post(url, data, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("data", response.json())

    def test_client_list(self):
        Client.objects.create(name="Client A", is_active=True)
        url = reverse("ledger:list-or-create-clients")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.json())

    def test_client_invalid_data(self):
        url = reverse("ledger:list-or-create-clients")
        response = self.client.post(url, {}, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_permission_denied(self):
        self.client.force_authenticate(user=None)
        url = reverse("ledger:list-or-create-clients")
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_sites_list(self):
        url = reverse("ledger:list-or-create-sites")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sites_create_validation_error(self):
        url = reverse("ledger:list-or-create-sites")
        response = self.client.post(url, {}, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vendors_list(self):
        url = reverse("ledger:list-or-create-vendors")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vendors_create_validation_error(self):
        url = reverse("ledger:list-or-create-vendors")
        response = self.client.post(url, {}, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subcontractors_list(self):
        url = reverse("ledger:list-or-create-subcontractors")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_subcontractors_create_validation_error(self):
        url = reverse("ledger:list-or-create-subcontractors")
        response = self.client.post(url, {}, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vendor_types_list(self):
        url = reverse("ledger:list-vendor-types")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_scopes_list(self):
        url = reverse("ledger:list-scopes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_update_validation_error(self):
        client = Client.objects.create(name="To Update", is_active=True)
        url = reverse("ledger:update-client", kwargs={"clientId": client.id})
        response = self.client.patch(url, {}, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_site_update_validation_error(self):
        c = Client.objects.create(name="C", is_active=True)
        site = Site.objects.create(code="S1", name="Site 1", client=c, is_active=True)
        url = reverse("ledger:update-site", kwargs={"siteId": site.id})
        response = self.client.patch(url, {}, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
