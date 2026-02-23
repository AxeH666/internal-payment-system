"""
Phase 2.4.4 — DB-level constraint tests.
Force IntegrityError and confirm expected behavior.
"""

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.ledger.models import (
    Client,
    Site,
    VendorType,
    Vendor,
    SubcontractorScope,
    Subcontractor,
)
from apps.payments.models import PaymentBatch, PaymentRequest, SOAVersion
from apps.users.models import User


class TotalAmountIntegrityConstraintTests(TestCase):
    """total_amount must equal base_amount + extra_amount when not null."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="constraint_user",
            password="testpass123",
            display_name="Constraint User",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="Constraint Batch",
            status="DRAFT",
            created_by=self.user,
        )
        self.client_obj = Client.objects.create(name="C1")
        self.site = Site.objects.create(
            code="S1", name="Site 1", client=self.client_obj
        )
        self.vt = VendorType.objects.create(name="VT1")
        self.vendor = Vendor.objects.create(name="V1", vendor_type=self.vt)

    def test_total_amount_mismatch_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentRequest.objects.create(
                    batch=self.batch,
                    currency="USD",
                    created_by=self.user,
                    status="DRAFT",
                    entity_type="VENDOR",
                    vendor=self.vendor,
                    site=self.site,
                    base_amount=Decimal("10"),
                    extra_amount=Decimal("5"),
                    total_amount=Decimal("99"),  # wrong: should be 15
                    vendor_snapshot_name="V1",
                    site_snapshot_code="S1",
                )


class LegacyOrLedgerExclusiveConstraintTests(TestCase):
    """Legacy and ledger-driven fields are mutually exclusive."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="legacy_user",
            password="testpass123",
            display_name="Legacy User",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="Legacy Batch",
            status="DRAFT",
            created_by=self.user,
        )
        self.client_obj = Client.objects.create(name="C2")
        self.site = Site.objects.create(
            code="S2", name="Site 2", client=self.client_obj
        )
        self.vt = VendorType.objects.create(name="VT2")
        self.vendor = Vendor.objects.create(name="V2", vendor_type=self.vt)

    def test_both_legacy_and_ledger_set_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentRequest.objects.create(
                    batch=self.batch,
                    currency="USD",
                    created_by=self.user,
                    status="DRAFT",
                    entity_type="VENDOR",
                    beneficiary_name="Legacy Name",
                    vendor=self.vendor,
                    site=self.site,
                    base_amount=Decimal("10"),
                    extra_amount=Decimal("0"),
                    total_amount=Decimal("10"),
                    vendor_snapshot_name="V2",
                    site_snapshot_code="S2",
                )


class VendorOrSubcontractorExclusiveConstraintTests(TestCase):
    """Vendor and subcontractor FKs are mutually exclusive (or both null)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="vendor_user",
            password="testpass123",
            display_name="Vendor User",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="Vendor Batch",
            status="DRAFT",
            created_by=self.user,
        )
        self.client_obj = Client.objects.create(name="C3")
        self.site = Site.objects.create(
            code="S3", name="Site 3", client=self.client_obj
        )
        self.vt = VendorType.objects.create(name="VT3")
        self.vendor = Vendor.objects.create(name="V3", vendor_type=self.vt)
        self.scope = SubcontractorScope.objects.create(name="SC3")
        self.sub = Subcontractor.objects.create(name="Sub3", scope=self.scope)

    def test_both_vendor_and_subcontractor_set_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentRequest.objects.create(
                    batch=self.batch,
                    currency="USD",
                    created_by=self.user,
                    status="DRAFT",
                    entity_type="VENDOR",
                    vendor=self.vendor,
                    subcontractor=self.sub,
                    site=self.site,
                    base_amount=Decimal("10"),
                    extra_amount=Decimal("0"),
                    total_amount=Decimal("10"),
                    vendor_snapshot_name="V3",
                    site_snapshot_code="S3",
                )


class UniqueRequestVersionConstraintTests(TestCase):
    """SOAVersion (payment_request, version_number) must be unique."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="soa_user",
            password="testpass123",
            display_name="SOA User",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="SOA Batch",
            status="DRAFT",
            created_by=self.user,
        )
        self.req = PaymentRequest.objects.create(
            batch=self.batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="Ben",
            beneficiary_account="ACC",
            purpose="P",
            amount=Decimal("100"),
        )

    def test_duplicate_version_number_raises_integrity_error(self):
        SOAVersion.objects.create(
            payment_request=self.req,
            version_number=1,
            document_reference="ref1",
            source="UPLOAD",
            uploaded_at=timezone.now(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SOAVersion.objects.create(
                    payment_request=self.req,
                    version_number=1,
                    document_reference="ref2",
                    source="UPLOAD",
                    uploaded_at=timezone.now(),
                )
