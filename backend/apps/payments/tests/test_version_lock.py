"""
Phase 2.4.6 — Version Lock Concurrency Test.

Two different idempotency keys attempting approval: first succeeds, second must fail.
Protects against different-key race (version locking), not just same-key replay.
"""

from rest_framework.test import APITestCase, APIClient

from apps.audit.models import AuditLog
from apps.payments.models import ApprovalRecord, PaymentRequest
from apps.users.models import User


class VersionLockConcurrencyTests(APITestCase):
    """Double approval with different keys: second 409/400, no duplicate effects."""

    def test_double_approval_with_different_keys_fails_second(self):
        client = APIClient()

        # Create users
        creator = User.objects.create_user(
            username="vl_creator",
            password="pass",
            display_name="VL Creator",
            role="CREATOR",
        )
        approver = User.objects.create_user(
            username="vl_approver",
            password="pass",
            display_name="VL Approver",
            role="APPROVER",
        )

        # Create batch + request
        client.force_authenticate(user=creator)
        batch_resp = client.post(
            "/api/v1/batches",
            {"title": "VL Batch"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="vl-batch-key",
        )
        self.assertIn(
            batch_resp.status_code,
            [200, 201],
            getattr(batch_resp, "data", batch_resp.content),
        )
        batch_id = batch_resp.data["data"]["id"]

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
            HTTP_IDEMPOTENCY_KEY="vl-create-key",
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
            HTTP_IDEMPOTENCY_KEY="vl-submit-key",
        )
        self.assertEqual(
            submit_resp.status_code,
            200,
            getattr(submit_resp, "data", submit_resp.content),
        )

        # First approval
        client.force_authenticate(user=approver)
        resp1 = client.post(
            f"/api/v1/requests/{request_id}/approve",
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY="vl-approve-key-1",
        )
        self.assertEqual(resp1.status_code, 200, getattr(resp1, "data", resp1.content))

        # Second approval (different key)
        resp2 = client.post(
            f"/api/v1/requests/{request_id}/approve",
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY="vl-approve-key-2",
        )

        self.assertIn(
            resp2.status_code,
            [409, 400],
            "Second approval with different key must return 409 or 400",
        )

        # Invariants: only one ApprovalRecord, one audit, request remains APPROVED
        self.assertEqual(
            ApprovalRecord.objects.filter(payment_request_id=request_id).count(),
            1,
            "Exactly one ApprovalRecord must exist",
        )
        self.assertEqual(
            AuditLog.objects.filter(
                entity_id=request_id,
                event_type="APPROVAL_RECORDED",
            ).count(),
            1,
            "Exactly one APPROVAL_RECORDED audit must exist",
        )
        request_obj = PaymentRequest.objects.get(id=request_id)
        self.assertEqual(
            request_obj.status,
            "APPROVED",
            "Request status must remain APPROVED",
        )
