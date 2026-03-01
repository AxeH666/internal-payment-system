"""
Invariant tests - protect architecture during development.
Run these tests before and after each implementation step.
"""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.payments.models import PaymentBatch, PaymentRequest, SOAVersion
from apps.users.models import User


class InvariantTests(TestCase):
    """Test critical system invariants."""

    def test_total_amount_integrity(self):
        """Ledger-driven requests: total_amount = base_amount + extra_amount."""
        from decimal import Decimal
        from apps.ledger.models import Client, Site, VendorType, Vendor

        user = User.objects.create_user(
            username="amt_user",
            password="testpass123",
            display_name="Amt User",
            role="CREATOR",
        )
        batch = PaymentBatch.objects.create(
            title="Amt Batch", status="DRAFT", created_by=user
        )
        client = Client.objects.create(name="Amt Client")
        site = Site.objects.create(code="AMT", name="Amt Site", client=client)
        vt = VendorType.objects.create(name="Amt VT")
        vendor = Vendor.objects.create(name="Amt Vendor", vendor_type=vt)
        req = PaymentRequest.objects.create(
            batch=batch,
            currency="USD",
            created_by=user,
            status="DRAFT",
            entity_type="VENDOR",
            vendor=vendor,
            site=site,
            base_amount=Decimal("10"),
            extra_amount=Decimal("5"),
            total_amount=Decimal("15"),
            vendor_snapshot_name="Amt Vendor",
            site_snapshot_code="AMT",
        )
        self.assertEqual(req.total_amount, req.base_amount + req.extra_amount)

    def test_idempotency_prevents_duplicates(self):
        """Verify idempotency keys prevent duplicate operations."""
        from decimal import Decimal
        from apps.payments import services

        user = User.objects.create_user(
            username="idem_inv_user",
            password="testpass123",
            display_name="Idem Inv User",
            role="CREATOR",
        )
        batch = PaymentBatch.objects.create(
            title="Idem Inv Batch", status="DRAFT", created_by=user
        )
        key = "invariant-idem-key-001"

        req1 = services.add_request(
            batch.id,
            user.id,
            amount=Decimal("100.00"),
            currency="USD",
            beneficiary_name="Inv Beneficiary",
            beneficiary_account="INV001",
            purpose="Invariant test payment",
            idempotency_key=key,
        )
        req2 = services.add_request(
            batch.id,
            user.id,
            amount=Decimal("100.00"),
            currency="USD",
            beneficiary_name="Inv Beneficiary",
            beneficiary_account="INV001",
            purpose="Invariant test payment",
            idempotency_key=key,
        )

        # Same idempotency key must return the same object
        self.assertEqual(req1.id, req2.id)
        # Only ONE PaymentRequest must exist in the DB
        self.assertEqual(PaymentRequest.objects.filter(batch=batch).count(), 1)

    def test_version_lock_prevents_double_approval(self):
        """Verify version locking prevents concurrent approval."""
        from decimal import Decimal
        from apps.payments import services
        from apps.payments.models import ApprovalRecord

        creator = User.objects.create_user(
            username="vl_inv_creator",
            password="testpass123",
            display_name="VL Inv Creator",
            role="CREATOR",
        )
        approver = User.objects.create_user(
            username="vl_inv_approver",
            password="testpass123",
            display_name="VL Inv Approver",
            role="APPROVER",
        )
        batch = PaymentBatch.objects.create(
            title="VL Inv Batch", status="DRAFT", created_by=creator
        )
        req = services.add_request(
            batch.id,
            creator.id,
            amount=Decimal("200.00"),
            currency="USD",
            beneficiary_name="VL Beneficiary",
            beneficiary_account="VL001",
            purpose="Version lock test",
            idempotency_key="vl-inv-add-001",
        )
        services.submit_batch(batch.id, creator.id)
        req.refresh_from_db()

        # First approval — must succeed
        services.approve_request(req.id, approver.id, comment="First approval")

    # Second approval — service correctly rejects it, but no duplicate record must exist
    from core.exceptions import InvalidStateError

    req.refresh_from_db()
    try:
        services.approve_request(req.id, approver.id, comment="Second approval attempt")
    except InvalidStateError:
        pass  # Expected — request already approved, this is correct behaviour

        # Exactly ONE ApprovalRecord must exist — never two
        self.assertEqual(ApprovalRecord.objects.filter(payment_request=req).count(), 1)

    def test_snapshots_required_for_ledger_driven(self):
        """Verify ledger-driven requests must have snapshots."""
        from decimal import Decimal
        from apps.payments import services
        from apps.ledger.models import Client, Site, VendorType, Vendor

        creator = User.objects.create_user(
            username="snap_inv_creator",
            password="testpass123",
            display_name="Snap Inv Creator",
            role="CREATOR",
        )
        batch = PaymentBatch.objects.create(
            title="Snap Inv Batch", status="DRAFT", created_by=creator
        )
        client = Client.objects.create(name="Snap Inv Client")
        site = Site.objects.create(code="SNP", name="Snap Inv Site", client=client)
        vt = VendorType.objects.create(name="Snap Inv VT")
        vendor = Vendor.objects.create(name="Snap Inv Vendor", vendor_type=vt)

        req = services.add_request(
            batch.id,
            creator.id,
            entity_type="VENDOR",
            vendor_id=vendor.id,
            site_id=site.id,
            base_amount=Decimal("500.00"),
            extra_amount=Decimal("50.00"),
            extra_reason="Snapshot invariant test",
            currency="USD",
            idempotency_key="snap-inv-add-001",
        )

        # Service must auto-populate snapshots from ledger entities
        self.assertIsNotNone(req.vendor_snapshot_name)
        self.assertIsNotNone(req.site_snapshot_code)
        self.assertEqual(req.vendor_snapshot_name, "Snap Inv Vendor")
        self.assertEqual(req.site_snapshot_code, "SNP")
        # Total amount integrity must hold
        self.assertEqual(req.total_amount, req.base_amount + req.extra_amount)


class SOAVersionConstraintTests(TestCase):
    """Test SOA version_number DB constraint (>= 1)."""

    def test_version_number_zero_fails(self):
        user = User.objects.create_user(
            username="soa_test_user",
            password="testpass123",
            display_name="SOA Tester",
            role="CREATOR",
        )

        batch = PaymentBatch.objects.create(
            title="Test Batch",
            status="DRAFT",
            created_by=user,
        )

        request = PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=user,
            beneficiary_name="Test Beneficiary",
        )

        with self.assertRaises(IntegrityError):
            SOAVersion.objects.create(
                payment_request=request,
                version_number=0,
                document_reference="doc-0",
                uploaded_at=timezone.now(),
                source="UPLOAD",
            )
