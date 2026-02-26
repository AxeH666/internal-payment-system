"""
STEP 5C — SOA export coverage.

API-level tests for GET /api/v1/batches/{batch_id}/soa-export?format=pdf|excel.
Uses real DB, no mocking. Covers soa_export.py (export_batch_soa_pdf, export_batch_soa_excel).
View export_batch_soa is covered in test_payments_views_coverage.py.
"""

from decimal import Decimal

from django.test import TestCase

from apps.payments.models import PaymentBatch, PaymentRequest, SOAVersion
from apps.payments.soa_export import export_batch_soa_pdf, export_batch_soa_excel
from apps.users.models import User


class SOAExportCoverageTests(TestCase):
    """SOA export PDF and Excel — soa_export.py branch coverage (real DB, no mocking)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="soa_export_user",
            password="testpass123",
            display_name="SOA Export User",
            role="CREATOR",
        )

    def _assert_pdf(self, content, filename, batch_title, min_length=100):
        self.assertGreater(len(content), min_length)
        self.assertTrue(content.startswith(b"%PDF-"), "PDF magic")
        self.assertIn("soa_export", filename)
        self.assertIn(batch_title.replace(" ", "_"), filename)

    def _assert_excel(self, content, filename, min_length=100):
        self.assertGreater(len(content), min_length)
        self.assertIn(".xlsx", filename)
        self.assertIn("soa_export", filename)
        self.assertTrue(content.startswith(b"PK"), "xlsx is zip")

    # --- Phase A: PDF ---

    def test_soa_export_pdf_empty_batch(self):
        """Empty batch → PDF: content, filename, Batch Total 0."""
        batch = PaymentBatch.objects.create(
            title="EmptyBatch",
            status="DRAFT",
            created_by=self.user,
        )
        content, filename = export_batch_soa_pdf(batch.id)
        self._assert_pdf(content, filename, batch.title)

    def test_soa_export_pdf_one_request_no_soa(self):
        """One request, no SOA → PDF with 'No SOA documents attached'."""
        batch = PaymentBatch.objects.create(
            title="OneNoSOA",
            status="DRAFT",
            created_by=self.user,
        )
        PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="Ben",
            beneficiary_account="ACC",
            purpose="Test",
            amount=Decimal("100.00"),
        )
        content, filename = export_batch_soa_pdf(batch.id)
        self._assert_pdf(content, filename, batch.title)

    def test_soa_export_pdf_one_request_one_soa(self):
        """One request, one SOA → PDF with SOA table."""
        batch = PaymentBatch.objects.create(
            title="OneWithSOA",
            status="DRAFT",
            created_by=self.user,
        )
        req = PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="Alice",
            beneficiary_account="ACC1",
            purpose="P1",
            amount=Decimal("50.00"),
        )
        SOAVersion.objects.create(
            payment_request=req,
            version_number=1,
            document_reference="doc/ref1",
            source="UPLOAD",
            uploaded_by=self.user,
        )
        content, filename = export_batch_soa_pdf(batch.id)
        self._assert_pdf(content, filename, batch.title)

    def test_soa_export_pdf_multiple_requests_mixed_soa(self):
        """Multiple requests, some with SOA, some without → PDF."""
        batch = PaymentBatch.objects.create(
            title="MixedSOA",
            status="DRAFT",
            created_by=self.user,
        )
        r1 = PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="A",
            beneficiary_account="A1",
            purpose="P1",
            amount=Decimal("10.00"),
        )
        r2 = PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="B",
            beneficiary_account="B1",
            purpose="P2",
            amount=Decimal("20.00"),
        )
        SOAVersion.objects.create(
            payment_request=r1,
            version_number=1,
            document_reference="d1",
            source="UPLOAD",
            uploaded_by=self.user,
        )
        content, filename = export_batch_soa_pdf(batch.id)
        self._assert_pdf(content, filename, batch.title)

    # --- Phase B: Excel ---

    def test_soa_export_excel_empty_batch(self):
        """Empty batch → Excel: content, filename, non-empty body."""
        batch = PaymentBatch.objects.create(
            title="EmptyExcel",
            status="DRAFT",
            created_by=self.user,
        )
        content, filename = export_batch_soa_excel(batch.id)
        self._assert_excel(content, filename)

    def test_soa_export_excel_one_request_no_soa(self):
        """One request, no SOA → Excel row with '—' for SOA columns."""
        batch = PaymentBatch.objects.create(
            title="ExcelNoSOA",
            status="DRAFT",
            created_by=self.user,
        )
        PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="C",
            beneficiary_account="C1",
            purpose="P",
            amount=Decimal("75.00"),
        )
        content, filename = export_batch_soa_excel(batch.id)
        self._assert_excel(content, filename)

    def test_soa_export_excel_one_request_with_soa(self):
        """One request, with SOA → Excel with SOA rows."""
        batch = PaymentBatch.objects.create(
            title="ExcelWithSOA",
            status="DRAFT",
            created_by=self.user,
        )
        req = PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="D",
            beneficiary_account="D1",
            purpose="P",
            amount=Decimal("25.00"),
        )
        SOAVersion.objects.create(
            payment_request=req,
            version_number=1,
            document_reference="d2",
            source="UPLOAD",
            uploaded_by=self.user,
        )
        content, filename = export_batch_soa_excel(batch.id)
        self._assert_excel(content, filename)

    def test_soa_export_excel_multiple_requests_mixed(self):
        """Multiple requests, mixed SOA → Excel."""
        batch = PaymentBatch.objects.create(
            title="ExcelMixed",
            status="DRAFT",
            created_by=self.user,
        )
        r1 = PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="E",
            beneficiary_account="E1",
            purpose="P1",
            amount=Decimal("15.00"),
        )
        PaymentRequest.objects.create(
            batch=batch,
            status="DRAFT",
            currency="USD",
            created_by=self.user,
            beneficiary_name="F",
            beneficiary_account="F1",
            purpose="P2",
            amount=Decimal("35.00"),
        )
        SOAVersion.objects.create(
            payment_request=r1,
            version_number=1,
            document_reference="d3",
            source="UPLOAD",
            uploaded_by=None,
        )
        content, filename = export_batch_soa_excel(batch.id)
        self._assert_excel(content, filename)
