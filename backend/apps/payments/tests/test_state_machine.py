"""
Phase 2.4.1 — State machine tests.
Legal and illegal transitions must raise appropriate errors.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from core.exceptions import InvalidStateError
from apps.payments.state_machine import validate_transition
from apps.payments.models import PaymentBatch, PaymentRequest, ApprovalRecord
from apps.users.models import User


class StateMachineTransitionTests(TestCase):
    """Test validate_transition for PaymentRequest and PaymentBatch."""

    def test_legal_request_transitions(self):
        """Legal PaymentRequest transitions do not raise."""
        # DRAFT -> SUBMITTED
        validate_transition("PaymentRequest", "DRAFT", "SUBMITTED")
        # SUBMITTED -> PENDING_APPROVAL
        validate_transition("PaymentRequest", "SUBMITTED", "PENDING_APPROVAL")
        # PENDING_APPROVAL -> APPROVED
        validate_transition("PaymentRequest", "PENDING_APPROVAL", "APPROVED")
        # PENDING_APPROVAL -> REJECTED
        validate_transition("PaymentRequest", "PENDING_APPROVAL", "REJECTED")
        # APPROVED -> PAID
        validate_transition("PaymentRequest", "APPROVED", "PAID")
        # DRAFT -> DRAFT (edit, no state change)
        validate_transition("PaymentRequest", "DRAFT", "DRAFT")

    def test_legal_batch_transitions(self):
        """Legal PaymentBatch transitions do not raise."""
        validate_transition("PaymentBatch", "DRAFT", "SUBMITTED")
        validate_transition("PaymentBatch", "DRAFT", "CANCELLED")
        validate_transition("PaymentBatch", "SUBMITTED", "PROCESSING")
        validate_transition("PaymentBatch", "PROCESSING", "COMPLETED")

    def test_illegal_draft_to_paid(self):
        """DRAFT -> PAID is invalid."""
        with self.assertRaises(InvalidStateError) as ctx:
            validate_transition("PaymentRequest", "DRAFT", "PAID")
        self.assertIn("Invalid transition", str(ctx.exception))

    def test_illegal_rejected_to_approved(self):
        """REJECTED -> APPROVED is invalid (terminal)."""
        with self.assertRaises(InvalidStateError) as ctx:
            validate_transition("PaymentRequest", "REJECTED", "APPROVED")
        self.assertIn("terminal", str(ctx.exception).lower())

    def test_illegal_completed_to_submitted(self):
        """COMPLETED -> SUBMITTED is invalid (batch terminal)."""
        with self.assertRaises(InvalidStateError) as ctx:
            validate_transition("PaymentBatch", "COMPLETED", "SUBMITTED")
        self.assertIn("terminal", str(ctx.exception).lower())

    def test_illegal_paid_to_approved(self):
        """PAID -> APPROVED is invalid."""
        with self.assertRaises(InvalidStateError) as ctx:
            validate_transition("PaymentRequest", "PAID", "APPROVED")
        self.assertIn("terminal", str(ctx.exception).lower())


class StateMachineAPIIllegalTransitionTests(TestCase):
    """Test that illegal transitions via API return 409 or validation error."""

    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username="sm_creator",
            password="testpass123",
            display_name="SM Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="sm_approver",
            password="testpass123",
            display_name="SM Approver",
            role="APPROVER",
        )
        self.client.force_authenticate(user=self.creator)
        self.batch = PaymentBatch.objects.create(
            title="SM Batch",
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
            amount=100,
        )

    def test_approve_already_approved_returns_409(self):
        """APPROVED -> APPROVED (second approval, different key) returns 409."""
        self.req.status = "APPROVED"
        self.req.save()
        ApprovalRecord.objects.create(
            payment_request=self.req,
            approver=self.approver,
            decision="APPROVED",
            comment="First",
        )
        self.client.force_authenticate(user=self.approver)
        url = f"/api/v1/requests/{self.req.id}/approve"
        payload = {"comment": "Second approval"}
        headers = {"HTTP_IDEMPOTENCY_KEY": "different-key-999"}
        response = self.client.post(url, payload, format="json", **headers)
        self.assertIn(
            response.status_code,
            [409, 400],
            "Double approval with different key must return 409 or 400",
        )

    def test_mark_paid_from_draft_returns_error(self):
        """Mark paid on DRAFT returns 400/409 (invalid state) or 403 (forbidden)."""
        self.client.force_authenticate(user=self.approver)
        url = f"/api/v1/requests/{self.req.id}/mark-paid"
        headers = {"HTTP_IDEMPOTENCY_KEY": "mark-draft-key"}
        response = self.client.post(url, {}, format="json", **headers)
        self.assertIn(
            response.status_code,
            [400, 409, 403],
            "Mark paid on DRAFT must not succeed (invalid state or forbidden)",
        )

    def test_reject_already_paid_returns_error(self):
        """Reject on PAID request returns error."""
        self.req.status = "PAID"
        self.req.save()
        self.client.force_authenticate(user=self.approver)
        url = f"/api/v1/requests/{self.req.id}/reject"
        payload = {"comment": "No"}
        headers = {"HTTP_IDEMPOTENCY_KEY": "reject-paid-key"}
        response = self.client.post(url, payload, format="json", **headers)
        self.assertIn(response.status_code, [400, 409])
