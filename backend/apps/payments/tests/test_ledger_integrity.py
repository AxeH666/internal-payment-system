"""
Phase 2.4.3 — Ledger integrity tests.
Inactive entities cannot be used; snapshot and exclusivity enforced.
"""

from decimal import Decimal

from django.test import TestCase

from core.exceptions import NotFoundError, ValidationError
from apps.ledger.models import (
    Client,
    Site,
    VendorType,
    Vendor,
    SubcontractorScope,
    Subcontractor,
)
from apps.payments.models import PaymentBatch
from apps.payments import services
from apps.users.models import User


class LedgerIntegrityTests(TestCase):
    """Inactive vendor/subcontractor/site cannot be used for ledger-driven requests."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="ledger_creator",
            password="testpass123",
            display_name="Ledger Creator",
            role="CREATOR",
        )
        self.client_obj = Client.objects.create(name="Ledger Client")
        self.site_active = Site.objects.create(
            code="SITE-A", name="Site A", client=self.client_obj, is_active=True
        )
        self.site_inactive = Site.objects.create(
            code="SITE-B", name="Site B", client=self.client_obj, is_active=False
        )
        self.vt = VendorType.objects.create(name="Type1")
        self.vendor_active = Vendor.objects.create(
            name="Vendor Active", vendor_type=self.vt, is_active=True
        )
        self.vendor_inactive = Vendor.objects.create(
            name="Vendor Inactive", vendor_type=self.vt, is_active=False
        )
        self.scope = SubcontractorScope.objects.create(name="Scope1")
        self.sub_active = Subcontractor.objects.create(
            name="Sub Active", scope=self.scope, is_active=True
        )
        self.sub_inactive = Subcontractor.objects.create(
            name="Sub Inactive", scope=self.scope, is_active=False
        )
        self.batch = PaymentBatch.objects.create(
            title="Ledger Batch",
            status="DRAFT",
            created_by=self.creator,
        )

    def test_inactive_vendor_cannot_be_used(self):
        with self.assertRaises(NotFoundError) as ctx:
            services.add_request(
                self.batch.id,
                self.creator.id,
                entity_type="VENDOR",
                vendor_id=self.vendor_inactive.id,
                site_id=self.site_active.id,
                base_amount=Decimal("100"),
                currency="USD",
            )
        self.assertIn("Active Vendor", str(ctx.exception))

    def test_inactive_subcontractor_cannot_be_used(self):
        with self.assertRaises(NotFoundError) as ctx:
            services.add_request(
                self.batch.id,
                self.creator.id,
                entity_type="SUBCONTRACTOR",
                subcontractor_id=self.sub_inactive.id,
                site_id=self.site_active.id,
                base_amount=Decimal("100"),
                currency="USD",
            )
        self.assertIn("Active Subcontractor", str(ctx.exception))

    def test_inactive_site_cannot_be_used(self):
        with self.assertRaises(NotFoundError) as ctx:
            services.add_request(
                self.batch.id,
                self.creator.id,
                entity_type="VENDOR",
                vendor_id=self.vendor_active.id,
                site_id=self.site_inactive.id,
                base_amount=Decimal("100"),
                currency="USD",
            )
        self.assertIn("Active Site", str(ctx.exception))

    def test_vendor_subcontractor_exclusivity_enforced(self):
        with self.assertRaises(ValidationError) as ctx:
            services.add_request(
                self.batch.id,
                self.creator.id,
                entity_type="VENDOR",
                vendor_id=self.vendor_active.id,
                subcontractor_id=self.sub_active.id,
                site_id=self.site_active.id,
                base_amount=Decimal("100"),
                currency="USD",
            )
        self.assertIn("Cannot specify both", str(ctx.exception))

    def test_ledger_driven_request_has_snapshot_fields(self):
        req = services.add_request(
            self.batch.id,
            self.creator.id,
            entity_type="VENDOR",
            vendor_id=self.vendor_active.id,
            site_id=self.site_active.id,
            base_amount=Decimal("50"),
            extra_amount=Decimal("10"),
            extra_reason="Fee",
            currency="USD",
        )
        self.assertIsNotNone(req.vendor_snapshot_name)
        self.assertEqual(req.vendor_snapshot_name, self.vendor_active.name)
        self.assertIsNotNone(req.site_snapshot_code)
        self.assertEqual(req.site_snapshot_code, self.site_active.code)
        self.assertIsNotNone(req.total_amount)
        self.assertEqual(req.total_amount, Decimal("60"))
