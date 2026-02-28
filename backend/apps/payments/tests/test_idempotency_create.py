"""
Phase 2.3.2 — Functional idempotency tests for CREATE_PAYMENT_REQUEST.
API-level duplicate submission: same Idempotency-Key must not create two requests.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.payments.models import PaymentBatch, PaymentRequest
from apps.users.models import User


class IdempotencyCreateTests(TestCase):
    """Duplicate POST with same Idempotency-Key must yield single PaymentRequest."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="idem_user",
            password="testpass123",
            display_name="Idem User",
            role="CREATOR",
        )
        self.client.force_authenticate(user=self.user)

        self.batch = PaymentBatch.objects.create(
            title="Idem Batch",
            status="DRAFT",
            created_by=self.user,
        )

    def test_duplicate_create_with_same_idempotency_key(self):
        url = f"/api/v1/batches/{self.batch.id}/requests"

        payload = {
            "currency": "USD",
            "beneficiaryName": "Test Beneficiary",
            "beneficiaryAccount": "ACC-001",
            "purpose": "Test payment",
            "amount": 100,
        }

        headers = {"HTTP_IDEMPOTENCY_KEY": "duplicate-key-123"}

        # First call
        response1 = self.client.post(url, payload, format="json", **headers)
        self.assertIn(response1.status_code, [201, 200])

        # Second call with same key
        response2 = self.client.post(url, payload, format="json", **headers)

        # Should NOT create a second payment request
        self.assertEqual(
            PaymentRequest.objects.count(),
            1,
            "Duplicate idempotent call created multiple payment requests",
        )

        # Second response: 200 OK with existing object (true idempotent replay)
        self.assertEqual(response2.status_code, 200)
