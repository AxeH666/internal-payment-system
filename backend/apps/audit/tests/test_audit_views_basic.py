"""
Basic API coverage tests for apps.audit.views.

Covers audit log query endpoint: list, filters, permission.
"""

import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from apps.audit.models import AuditLog


class AuditViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="audit_user",
            password="testpass123",
            display_name="Audit User",
            role="ADMIN",
        )
        self.client.force_authenticate(self.user)

    def test_audit_list(self):
        AuditLog.objects.create(
            event_type="TEST",
            actor=self.user,
            entity_type="PaymentBatch",
            entity_id=uuid.uuid4(),
        )
        url = reverse("audit:query-audit-log")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.json())

    def test_audit_list_logs_alias(self):
        url = reverse("audit:query-audit-logs")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_audit_filter_entity_type_valid(self):
        url = reverse("audit:query-audit-log")
        response = self.client.get(url, {"entityType": "PaymentBatch"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_audit_filter_entity_type_invalid(self):
        url = reverse("audit:query-audit-log")
        response = self.client.get(url, {"entityType": "InvalidType"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_audit_unauthorized(self):
        self.client.force_authenticate(user=None)
        url = reverse("audit:query-audit-log")
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
