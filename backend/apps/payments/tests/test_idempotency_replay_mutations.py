"""
Phase 2.4.5 — Automated Idempotency Replay Tests.

Same idempotency key replay must return 200 and must not create duplicate
side effects: ApprovalRecord, APPROVAL_RECORDED audit, REQUEST_PAID audit.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.payments.models import ApprovalRecord, PaymentBatch, PaymentRequest
from apps.payments import services
from apps.users.models import User


def _idem_headers(key):
    return {"HTTP_IDEMPOTENCY_KEY": key}


class IdempotencyApproveReplayTests(TestCase):
    """Same-key approve replay returns 200 and no duplicate side effects."""

    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username="replay_creator",
            password="testpass123",
            display_name="Replay Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="replay_approver",
            password="testpass123",
            display_name="Replay Approver",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="Approve Replay Batch",
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

    def test_approve_replay_returns_200_and_no_duplicate_side_effects(self):
        url = f"/api/v1/requests/{self.req.id}/approve"
        payload = {"comment": "Approve"}
        key = "approve-replay-key"
        headers = _idem_headers(key)

        self.client.force_authenticate(user=self.approver)
        response1 = self.client.post(url, payload, format="json", **headers)
        self.assertEqual(response1.status_code, 200, "First approve must succeed")

        response2 = self.client.post(url, payload, format="json", **headers)
        self.assertEqual(
            response2.status_code,
            200,
            "Replay with same idempotency key must return 200",
        )
        self.assertEqual(
            ApprovalRecord.objects.filter(payment_request=self.req).count(),
            1,
            "Exactly one ApprovalRecord must exist",
        )
        approval_audit = AuditLog.objects.filter(
            entity_id=self.req.id, event_type="APPROVAL_RECORDED"
        )
        self.assertEqual(
            approval_audit.count(),
            1,
            "Exactly one APPROVAL_RECORDED audit must exist",
        )


class IdempotencyRejectReplayTests(TestCase):
    """Same-key reject replay returns 200 and no duplicate side effects."""

    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username="reject_replay_creator",
            password="testpass123",
            display_name="Reject Replay Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="reject_replay_approver",
            password="testpass123",
            display_name="Reject Replay Approver",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="Reject Replay Batch",
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

    def test_reject_replay_returns_200_and_no_duplicate_side_effects(self):
        url = f"/api/v1/requests/{self.req.id}/reject"
        payload = {"comment": "Reject"}
        key = "reject-replay-key"
        headers = _idem_headers(key)

        self.client.force_authenticate(user=self.approver)
        response1 = self.client.post(url, payload, format="json", **headers)
        self.assertEqual(response1.status_code, 200, "First reject must succeed")

        response2 = self.client.post(url, payload, format="json", **headers)
        self.assertEqual(
            response2.status_code,
            200,
            "Replay with same idempotency key must return 200",
        )
        self.assertEqual(
            ApprovalRecord.objects.filter(payment_request=self.req).count(),
            1,
            "Exactly one ApprovalRecord must exist",
        )
        approval_audit = AuditLog.objects.filter(
            entity_id=self.req.id, event_type="APPROVAL_RECORDED"
        )
        self.assertEqual(
            approval_audit.count(),
            1,
            "Exactly one APPROVAL_RECORDED audit must exist",
        )


class IdempotencyMarkPaidReplayTests(TestCase):
    """Same-key mark_paid replay returns 200 and no duplicate REQUEST_PAID audit."""

    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username="mp_replay_creator",
            password="testpass123",
            display_name="MarkPaid Replay Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="mp_replay_approver",
            password="testpass123",
            display_name="MarkPaid Replay Approver",
            role="APPROVER",
        )
        self.admin = User.objects.create_user(
            username="mp_replay_admin",
            password="testpass123",
            display_name="MarkPaid Replay Admin",
            role="ADMIN",
        )
        self.batch = PaymentBatch.objects.create(
            title="MarkPaid Replay Batch",
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
        services.approve_request(
            self.req.id,
            self.approver.id,
            comment="Approve",
            idempotency_key="mp-approve-key",
        )
        self.req.refresh_from_db()

    def test_mark_paid_replay_returns_200_and_no_duplicate_paid_audit(self):
        url = f"/api/v1/requests/{self.req.id}/mark-paid"
        key = "mark-paid-replay-key"
        headers = _idem_headers(key)

        self.client.force_authenticate(user=self.admin)
        response1 = self.client.post(url, {}, format="json", **headers)
        self.assertEqual(response1.status_code, 200, "First mark_paid must succeed")

        response2 = self.client.post(url, {}, format="json", **headers)
        self.assertEqual(
            response2.status_code,
            200,
            "Replay with same idempotency key must return 200",
        )
        paid_audit = AuditLog.objects.filter(
            entity_id=self.req.id, event_type="REQUEST_PAID"
        )
        self.assertEqual(
            paid_audit.count(),
            1,
            "Exactly one REQUEST_PAID audit must exist",
        )
        self.req.refresh_from_db()
        self.assertEqual(
            self.req.status,
            "PAID",
            "Request status must be PAID",
        )
