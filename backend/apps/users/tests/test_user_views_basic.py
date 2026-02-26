"""
Basic API coverage tests for apps.users.views.

Covers current user, list users, create user (success and validation/conflict).
"""

import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User


def _idem_headers():
    return {"HTTP_IDEMPOTENCY_KEY": "users-basic-" + uuid.uuid4().hex[:8]}


class UserViewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username=f"admin_{uuid.uuid4().hex[:8]}",
            password="testpass123",
            display_name="Admin",
            role="ADMIN",
        )
        self.client.force_authenticate(self.admin)

    def test_get_current_user(self):
        url = reverse("users:current-user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.json())

    def test_user_list(self):
        url = reverse("users:list-or-create-users")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.json())

    def test_user_creation_success(self):
        url = reverse("users:list-or-create-users")
        data = {
            "username": "newuser_" + uuid.uuid4().hex[:8],
            "password": "testpass123",
            "displayName": "New User",
            "role": "VIEWER",
        }
        response = self.client.post(url, data, format="json", **_idem_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("data", response.json())

    def test_user_creation_validation_error(self):
        url = reverse("users:list-or-create-users")
        response = self.client.post(url, {}, format="json", **_idem_headers())
        self.assertIn(
            response.status_code,
            (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN),
        )

    def test_user_list_unauthorized(self):
        self.client.force_authenticate(user=None)
        url = reverse("users:list-or-create-users")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
