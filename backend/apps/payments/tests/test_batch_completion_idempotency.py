"""
Phase 2.4.7 — Batch Completion Idempotency Test.

Replay of mark_paid with same idempotency key must NOT duplicate:
- Batch transition to COMPLETED
- SOA generation (SOAVersion rows)
- REQUEST_PAID audit
"""

from rest_framework.test import APITestCase, APIClient

from apps.audit.models import AuditLog
from apps.payments.models import PaymentBatch, PaymentRequest, SOAVersion
from apps.users.models import User


class BatchCompletionIdempotencyTests(APITestCase):
    """mark_paid replay must not duplicate batch completion or SOA generation."""

    def test_mark_paid_replay_does_not_duplicate_batch_completion(self):
        client = APIClient()

        # Users
        creator = User.objects.create_user(
            username="bc_creator",
            password="pass",
            display_name="BC Creator",
            role="CREATOR",
        )
        approver = User.objects.create_user(
            username="bc_approver",
            password="pass",
            display_name="BC Approver",
            role="APPROVER",
        )
        admin = User.objects.create_user(
            username="bc_admin",
            password="pass",
            display_name="BC Admin",
            role="ADMIN",
        )

        # Create batch
        client.force_authenticate(user=creator)
        batch_resp = client.post(
            "/api/v1/batches",
            {"title": "BC Batch"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="bc-batch-key",
        )
        self.assertIn(
            batch_resp.status_code,
            [200, 201],
            getattr(batch_resp, "data", batch_resp.content),
        )
        batch_id = batch_resp.data["data"]["id"]

        # Add request
        req_resp = client.post(
            f"/api/v1/batches/{batch_id}/requests",
            {
                "currency": "USD",
                "beneficiaryName": "Test",
                "beneficiaryAccount": "123",
                "purpose": "Test",
                "amount": 100,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="bc-create-key",
        )
        self.assertIn(
            req_resp.status_code,
            [200, 201],
            getattr(req_resp, "data", req_resp.content),
        )
        request_id = req_resp.data["data"]["id"]

        # Submit batch
        submit_resp = client.post(
            f"/api/v1/batches/{batch_id}/submit",
            format="json",
            HTTP_IDEMPOTENCY_KEY="bc-submit-key",
        )
        self.assertEqual(
            submit_resp.status_code,
            200,
            getattr(submit_resp, "data", submit_resp.content),
        )

        # Approve
        client.force_authenticate(user=approver)
        approve_resp = client.post(
            f"/api/v1/requests/{request_id}/approve",
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY="bc-approve-key",
        )
        self.assertEqual(
            approve_resp.status_code,
            200,
            getattr(approve_resp, "data", approve_resp.content),
        )

        # First mark_paid (batch completes, SOA generated)
        client.force_authenticate(user=admin)
        resp1 = client.post(
            f"/api/v1/requests/{request_id}/mark-paid",
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY="bc-paid-key",
        )
        self.assertEqual(resp1.status_code, 200, getattr(resp1, "data", resp1.content))

        # Replay mark_paid (same key — must not duplicate batch completion or SOA)
        resp2 = client.post(
            f"/api/v1/requests/{request_id}/mark-paid",
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY="bc-paid-key",
        )
        self.assertEqual(resp2.status_code, 200, getattr(resp2, "data", resp2.content))

        # Reload objects
        batch = PaymentBatch.objects.get(id=batch_id)
        request = PaymentRequest.objects.get(id=request_id)

        # Assertions: single transition, single SOA, single REQUEST_PAID audit
        self.assertEqual(request.status, "PAID", "Request must be PAID")
        self.assertEqual(batch.status, "COMPLETED", "Batch must be COMPLETED")

        self.assertEqual(
            AuditLog.objects.filter(
                entity_id=request_id,
                event_type="REQUEST_PAID",
            ).count(),
            1,
            "Exactly one REQUEST_PAID audit must exist",
        )

        self.assertEqual(
            SOAVersion.objects.filter(payment_request_id=request_id).count(),
            1,
            "Exactly one SOA version for this request "
            "(batch completion generates once)",
        )
