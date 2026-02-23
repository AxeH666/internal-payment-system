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
        # Test will be implemented as idempotency is added
        pass

    def test_version_lock_prevents_double_approval(self):
        """Verify version locking prevents concurrent approval."""
        # Test will be implemented as version locking is added
        pass

    def test_snapshots_required_for_ledger_driven(self):
        """Verify ledger-driven requests must have snapshots."""
        # Test will be implemented as snapshots are added
        pass


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
