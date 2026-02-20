"""
Authority and user API tests.
Phase 2: authority smoke test — no privilege escalation via API.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User


class AuthoritySmokeTests(TestCase):
    """Smoke tests for authority model: ADMIN cannot be created via API."""

    def setUp(self):
        self.client = APIClient()
        User.objects.create_superuser(
            username="admin_authority_test",
            password="testpass123",
        )
        # Get token for admin
        r = self.client.post(
            "/api/v1/auth/login",
            {"username": "admin_authority_test", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.token = r.data["data"]["token"]

    def test_cannot_create_admin_via_api(self):
        """POST /api/v1/users/ with role=ADMIN must return 400 and reject."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        r = self.client.post(
            "/api/v1/users/",
            {
                "username": "would_be_admin",
                "password": "pass123",
                "display_name": "Admin",
                "role": "ADMIN",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="authority-test-no-admin-via-api",
        )
        self.assertEqual(r.status_code, 400, r.data)
        # DRF serializer validation returns field errors or error wrapper
        msg = r.data.get("error", {}).get("message", "") or str(r.data)
        role_msgs = r.data.get("role", [])
        if isinstance(role_msgs, list):
            msg = msg + " " + " ".join(role_msgs)
        self.assertIn(
            "Cannot create ADMIN users via API",
            msg,
            f"Expected ADMIN creation rejection message; got: {r.data}",
        )
        self.assertFalse(User.objects.filter(username="would_be_admin").exists())
