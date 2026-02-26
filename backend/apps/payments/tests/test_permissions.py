"""
Phase 2.4.2 — Permission matrix tests.
Role enforcement: CREATOR, APPROVER, ADMIN, VIEWER per API action.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.payments.models import PaymentBatch, PaymentRequest
from apps.payments import services
from apps.users.models import User


def _idem_headers(key):
    return {"HTTP_IDEMPOTENCY_KEY": key}


class PermissionMatrixTests(TestCase):
    """Test role-based access for Create, Approve, Reject, Mark Paid."""

    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username="perm_creator",
            password="testpass123",
            display_name="Perm Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="perm_approver",
            password="testpass123",
            display_name="Perm Approver",
            role="APPROVER",
        )
        self.admin = User.objects.create_user(
            username="perm_admin",
            password="testpass123",
            display_name="Perm Admin",
            role="ADMIN",
        )
        self.viewer = User.objects.create_user(
            username="perm_viewer",
            password="testpass123",
            display_name="Perm Viewer",
            role="VIEWER",
        )
        self.batch = PaymentBatch.objects.create(
            title="Perm Batch",
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

    def test_creator_can_create_batch(self):
        self.client.force_authenticate(user=self.creator)
        r = self.client.post(
            "/api/v1/batches",
            {"title": "New Batch"},
            format="json",
            **_idem_headers("creator-batch"),
        )
        self.assertIn(r.status_code, [200, 201])

    def test_creator_can_add_request(self):
        self.client.force_authenticate(user=self.creator)
        r = self.client.post(
            f"/api/v1/batches/{self.batch.id}/requests",
            {
                "currency": "USD",
                "beneficiaryName": "X",
                "beneficiaryAccount": "A",
                "purpose": "P",
                "amount": 50,
            },
            format="json",
            **_idem_headers("creator-req"),
        )
        self.assertIn(r.status_code, [200, 201])

    def test_creator_cannot_approve(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.creator)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/approve",
            {"comment": "No"},
            format="json",
            **_idem_headers("creator-approve"),
        )
        self.assertEqual(r.status_code, 403)

    def test_creator_cannot_reject(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.creator)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/reject",
            {"comment": "No"},
            format="json",
            **_idem_headers("creator-reject"),
        )
        self.assertEqual(r.status_code, 403)

    def test_creator_cannot_mark_paid(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="perm-approve-1"
        )
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.creator)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/mark-paid",
            {},
            format="json",
            **_idem_headers("creator-markpaid"),
        )
        self.assertEqual(r.status_code, 403)

    def test_approver_cannot_create_batch(self):
        self.client.force_authenticate(user=self.approver)
        r = self.client.post(
            "/api/v1/batches",
            {"title": "Approver Batch"},
            format="json",
            **_idem_headers("approver-batch"),
        )
        self.assertEqual(r.status_code, 403)

    def test_approver_cannot_add_request(self):
        self.client.force_authenticate(user=self.approver)
        r = self.client.post(
            f"/api/v1/batches/{self.batch.id}/requests",
            {
                "currency": "USD",
                "beneficiaryName": "X",
                "beneficiaryAccount": "A",
                "purpose": "P",
                "amount": 50,
            },
            format="json",
            **_idem_headers("approver-req"),
        )
        self.assertEqual(r.status_code, 403)

    def test_approver_can_approve(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.approver)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/approve",
            {"comment": "OK"},
            format="json",
            **_idem_headers("approver-approve"),
        )
        self.assertEqual(r.status_code, 200)

    def test_approver_can_reject(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.approver)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/reject",
            {"comment": "No"},
            format="json",
            **_idem_headers("approver-reject"),
        )
        self.assertEqual(r.status_code, 200)

    def test_approver_cannot_mark_paid(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="perm-approve-mp"
        )
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.approver)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/mark-paid",
            {},
            format="json",
            **_idem_headers("approver-markpaid"),
        )
        self.assertEqual(r.status_code, 403)

    def test_admin_can_create_batch(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.post(
            "/api/v1/batches",
            {"title": "Admin Batch"},
            format="json",
            **_idem_headers("admin-batch"),
        )
        self.assertIn(r.status_code, [200, 201])

    def test_admin_can_approve(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.admin)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/approve",
            {"comment": "OK"},
            format="json",
            **_idem_headers("admin-approve"),
        )
        self.assertEqual(r.status_code, 200)

    def test_admin_can_mark_paid(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="perm-approve-admin"
        )
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.admin)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/mark-paid",
            {},
            format="json",
            **_idem_headers("admin-markpaid"),
        )
        self.assertEqual(r.status_code, 200)

    def test_viewer_cannot_create_batch(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.post(
            "/api/v1/batches",
            {"title": "Viewer Batch"},
            format="json",
            **_idem_headers("viewer-batch"),
        )
        self.assertEqual(r.status_code, 403)

    def test_viewer_cannot_add_request(self):
        self.client.force_authenticate(user=self.viewer)
        r = self.client.post(
            f"/api/v1/batches/{self.batch.id}/requests",
            {
                "currency": "USD",
                "beneficiaryName": "X",
                "beneficiaryAccount": "A",
                "purpose": "P",
                "amount": 50,
            },
            format="json",
            **_idem_headers("viewer-req"),
        )
        self.assertEqual(r.status_code, 403)

    def test_viewer_cannot_approve(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.viewer)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/approve",
            {"comment": "No"},
            format="json",
            **_idem_headers("viewer-approve"),
        )
        self.assertEqual(r.status_code, 403)

    def test_viewer_cannot_reject(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.viewer)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/reject",
            {"comment": "No"},
            format="json",
            **_idem_headers("viewer-reject"),
        )
        self.assertEqual(r.status_code, 403)

    def test_viewer_cannot_mark_paid(self):
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="perm-approve-viewer"
        )
        self.req.refresh_from_db()
        self.client.force_authenticate(user=self.viewer)
        r = self.client.post(
            f"/api/v1/requests/{self.req.id}/mark-paid",
            {},
            format="json",
            **_idem_headers("viewer-markpaid"),
        )
        self.assertEqual(r.status_code, 403)
