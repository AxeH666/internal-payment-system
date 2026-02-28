"""
Phase 3.1 — Structured logging: approve emits a structured log with correct fields.
Minimal test: when approve is called, a log entry with correct structure is emitted.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.payments.models import PaymentBatch, PaymentRequest
from apps.payments import services
from apps.users.models import User


class StructuredLoggingApproveTests(TestCase):
    """Approve request emits structured log with request_id, entity_id, operation."""

    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username="log_creator",
            password="testpass123",
            display_name="Log Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="log_approver",
            password="testpass123",
            display_name="Log Approver",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="Log Test Batch",
            status="DRAFT",
            created_by=self.creator,
        )
        self.req = PaymentRequest.objects.create(
            batch=self.batch,
            status="DRAFT",
            currency="USD",
            created_by=self.creator,
            beneficiary_name="Ben",
            beneficiary_account="ACC",
            purpose="P",
            amount=Decimal("100"),
        )
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()

    def test_approve_emits_structured_log_and_response_has_request_id(self):
        url = f"/api/v1/requests/{self.req.id}/approve"
        payload = {"comment": "Approve"}
        request_id = "test-correlation-id-12345"
        headers = {
            "HTTP_IDEMPOTENCY_KEY": "log-test-approve-key",
            "HTTP_X_REQUEST_ID": request_id,
        }

        self.client.force_authenticate(user=self.approver)
        with self.assertLogs("apps.payments.services", level="INFO") as cm:
            response = self.client.post(url, payload, format="json", **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("X-Request-ID"), request_id)

        approval_logs = [
            r
            for r in cm.records
            if getattr(r, "operation", None) == "APPROVE_PAYMENT_REQUEST"
        ]
        self.assertEqual(
            len(approval_logs), 1, "Exactly one APPROVE_PAYMENT_REQUEST log"
        )
        self.assertEqual(approval_logs[0].message, "payment_request_approved")
        self.assertEqual(approval_logs[0].entity_id, str(self.req.id))
        self.assertEqual(approval_logs[0].request_id, request_id)
