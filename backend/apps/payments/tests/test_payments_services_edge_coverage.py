"""
Phase 3 Step 5B — Payments services edge coverage.

Deep branch-coverage unit tests for apps/payments/services.py.
Priority: version lock → batch completion → invalid transitions →
idempotency replay → permission violations → SOA generation.
No mocking of state transitions; real DB objects; alternate branches hit deliberately.
"""

from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from core.exceptions import (
    InvalidStateError,
    NotFoundError,
    PermissionDeniedError,
    PreconditionFailedError,
    ValidationError,
)
from apps.audit.models import AuditLog
from apps.payments.models import (
    ApprovalRecord,
    PaymentBatch,
    PaymentRequest,
    SOAVersion,
)
from apps.payments import services
from apps.users.models import User

# -----------------------------------------------------------------------------
# 1. VERSION LOCK CONFLICTS
# Simulate version_locked_update returning 0 (concurrent modification).
# -----------------------------------------------------------------------------


class VersionLockConflictTests(TestCase):
    """Version lock conflict (updated_count == 0) in approve/reject/mark_paid."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="vl_creator",
            password="testpass123",
            display_name="VL Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="vl_approver",
            password="testpass123",
            display_name="VL Approver",
            role="APPROVER",
        )
        self.admin = User.objects.create_user(
            username="vl_admin",
            password="testpass123",
            display_name="VL Admin",
            role="ADMIN",
        )
        self.batch = PaymentBatch.objects.create(
            title="VL Batch",
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

    def test_approve_version_lock_conflict_raises_invalid_state(self):
        """version_locked_update returns 0 → approve raises InvalidStateError."""
        with patch(
            "apps.payments.services.version_locked_update",
            return_value=0,
        ):
            with self.assertRaises(InvalidStateError) as ctx:
                services.approve_request(
                    self.req.id,
                    self.approver.id,
                    comment="OK",
                    idempotency_key="vl-approve-key",
                )
            self.assertIn("Concurrent modification", str(ctx.exception.message))

    def test_reject_version_lock_conflict_raises_invalid_state(self):
        """version_locked_update returns 0 → reject_request raises InvalidStateError."""
        with patch(
            "apps.payments.services.version_locked_update",
            return_value=0,
        ):
            with self.assertRaises(InvalidStateError) as ctx:
                services.reject_request(
                    self.req.id,
                    self.approver.id,
                    comment="No",
                    idempotency_key="vl-reject-key",
                )
            self.assertIn("Concurrent modification", str(ctx.exception.message))

    def test_mark_paid_version_lock_conflict_raises_invalid_state(self):
        """When version_locked_update returns 0, mark_paid raises InvalidStateError."""
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="vl-mp-approve"
        )
        self.req.refresh_from_db()
        with patch(
            "apps.payments.services.version_locked_update",
            return_value=0,
        ):
            with self.assertRaises(InvalidStateError) as ctx:
                services.mark_paid(
                    self.req.id,
                    self.admin.id,
                    idempotency_key="vl-markpaid-key",
                )
            self.assertIn("Concurrent modification", str(ctx.exception.message))


# -----------------------------------------------------------------------------
# 2. BATCH COMPLETION LOGIC
# All terminal → COMPLETED + SOA; not all terminal → no completion;
# already COMPLETED → no double completion.
# -----------------------------------------------------------------------------


class BatchCompletionLogicTests(TestCase):
    """Batch completion and SOA generation trigger branches."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="bc_creator",
            password="testpass123",
            display_name="BC Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="bc_approver",
            password="testpass123",
            display_name="BC Approver",
            role="APPROVER",
        )
        self.admin = User.objects.create_user(
            username="bc_admin",
            password="testpass123",
            display_name="BC Admin",
            role="ADMIN",
        )
        self.batch = PaymentBatch.objects.create(
            title="BC Batch",
            status="DRAFT",
            created_by=self.creator,
        )
        self.req1 = PaymentRequest.objects.create(
            batch=self.batch,
            status="DRAFT",
            currency="USD",
            created_by=self.creator,
            beneficiary_name="R1",
            beneficiary_account="A1",
            purpose="P1",
            amount=Decimal("100"),
        )
        self.req2 = PaymentRequest.objects.create(
            batch=self.batch,
            status="DRAFT",
            currency="USD",
            created_by=self.creator,
            beneficiary_name="R2",
            beneficiary_account="A2",
            purpose="P2",
            amount=Decimal("200"),
        )
        services.submit_batch(self.batch.id, self.creator.id)
        self.req1.refresh_from_db()
        self.req2.refresh_from_db()

    def test_mark_paid_when_not_all_terminal_batch_stays_processing(self):
        """One PAID, other PENDING_APPROVAL → batch stays PROCESSING."""
        services.approve_request(
            self.req1.id, self.approver.id, idempotency_key="bc-approve-1"
        )
        # Do not approve req2 — so we have one APPROVED, one PENDING_APPROVAL
        services.mark_paid(self.req1.id, self.admin.id, idempotency_key="bc-mp-1")
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "PROCESSING")

    def test_mark_paid_when_all_terminal_batch_completes_and_soa_generated(self):
        """Mark last request PAID → batch COMPLETED and SOA generated."""
        services.approve_request(
            self.req1.id, self.approver.id, idempotency_key="bc-app-1"
        )
        services.approve_request(
            self.req2.id, self.approver.id, idempotency_key="bc-app-2"
        )
        self.req1.refresh_from_db()
        self.req2.refresh_from_db()
        services.mark_paid(self.req1.id, self.admin.id, idempotency_key="bc-mp-first")
        services.mark_paid(self.req2.id, self.admin.id, idempotency_key="bc-mp-second")
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "COMPLETED")
        self.assertIsNotNone(self.batch.completed_at)
        generated = SOAVersion.objects.filter(
            payment_request__batch=self.batch,
            source=SOAVersion.SOURCE_GENERATED,
        )
        self.assertEqual(generated.count(), 2)

    def test_generate_soa_for_batch_already_generated_returns_empty(self):
        """Idempotency: generate_soa_for_batch when SOA already generated returns []."""
        services.approve_request(
            self.req1.id, self.approver.id, idempotency_key="bc-sga-1"
        )
        services.approve_request(
            self.req2.id, self.approver.id, idempotency_key="bc-sga-2"
        )
        services.mark_paid(self.req1.id, self.admin.id, idempotency_key="bc-sga-mp1")
        services.mark_paid(self.req2.id, self.admin.id, idempotency_key="bc-sga-mp2")
        # generate_soa_for_batch already run by mark_paid; second call idempotent
        second = services.generate_soa_for_batch(self.batch.id)
        self.assertEqual(second, [])

    def test_generate_soa_for_batch_not_found_returns_empty(self):
        """generate_soa_for_batch with non-existent batch_id returns []."""
        import uuid

        result = services.generate_soa_for_batch(uuid.uuid4())
        self.assertEqual(result, [])


# -----------------------------------------------------------------------------
# 3. INVALID STATE TRANSITIONS
# Approve DRAFT; Reject PAID; Mark paid REJECTED/DRAFT; Submit cancelled; etc.
# -----------------------------------------------------------------------------


class InvalidStateTransitionTests(TestCase):
    """Invalid state transition branches raise InvalidStateError."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="ist_creator",
            password="testpass123",
            display_name="IST Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="ist_approver",
            password="testpass123",
            display_name="IST Approver",
            role="APPROVER",
        )
        self.admin = User.objects.create_user(
            username="ist_admin",
            password="testpass123",
            display_name="IST Admin",
            role="ADMIN",
        )
        self.batch = PaymentBatch.objects.create(
            title="IST Batch",
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

    def test_approve_draft_request_raises_invalid_state(self):
        """Approve when status is DRAFT (not submitted) → InvalidStateError."""
        with self.assertRaises(InvalidStateError):
            services.approve_request(
                self.req.id,
                self.approver.id,
                comment="OK",
                idempotency_key="ist-app-draft",
            )

    def test_approve_already_approved_raises_invalid_state(self):
        """Approve when already APPROVED → InvalidStateError."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="ist-app-first"
        )
        self.req.refresh_from_db()
        with self.assertRaises(InvalidStateError) as ctx:
            services.approve_request(
                self.req.id,
                self.approver.id,
                comment="Again",
                idempotency_key="ist-app-second",
            )
        self.assertIn("already been approved", str(ctx.exception.message))

    def test_reject_paid_request_raises_invalid_state(self):
        """Reject when status is PAID → InvalidStateError (not idempotent for PAID)."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="ist-rej-app"
        )
        services.mark_paid(self.req.id, self.admin.id, idempotency_key="ist-rej-mp")
        self.req.refresh_from_db()
        with self.assertRaises(InvalidStateError):
            services.reject_request(
                self.req.id,
                self.approver.id,
                comment="No",
                idempotency_key="ist-rej-paid",
            )

    def test_mark_paid_rejected_request_raises_invalid_state(self):
        """Mark paid when status is REJECTED → InvalidStateError."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.reject_request(
            self.req.id, self.approver.id, comment="No", idempotency_key="ist-mp-rej"
        )
        self.req.refresh_from_db()
        with self.assertRaises(InvalidStateError):
            services.mark_paid(
                self.req.id, self.admin.id, idempotency_key="ist-mp-rejected"
            )

    def test_mark_paid_draft_request_raises_invalid_state(self):
        """Mark paid when status is DRAFT → InvalidStateError."""
        with self.assertRaises(InvalidStateError):
            services.mark_paid(
                self.req.id, self.admin.id, idempotency_key="ist-mp-draft"
            )

    def test_submit_cancelled_batch_raises_invalid_state(self):
        """Submit batch when status is CANCELLED → InvalidStateError."""
        from django.utils import timezone

        # Reach CANCELLED in a way that satisfies DB (submitted_at set when not DRAFT)
        PaymentBatch.objects.filter(id=self.batch.id).update(
            status="CANCELLED",
            submitted_at=timezone.now(),
            completed_at=timezone.now(),
        )
        self.batch.refresh_from_db()
        with self.assertRaises(InvalidStateError):
            services.submit_batch(self.batch.id, self.creator.id)

    def test_cancel_submitted_batch_raises_invalid_state(self):
        """Cancel batch when status is not DRAFT → InvalidStateError."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.batch.refresh_from_db()
        with self.assertRaises(InvalidStateError):
            services.cancel_batch(self.batch.id, self.creator.id)

    def test_update_request_non_draft_raises_invalid_state(self):
        """Update request when status is not DRAFT → InvalidStateError."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        with self.assertRaises(InvalidStateError) as ctx:
            services.update_request(
                self.req.id,
                self.batch.id,
                self.creator.id,
                amount=Decimal("99"),
            )
        self.assertIn("Cannot update request", str(ctx.exception.message))

    def test_submit_empty_batch_raises_precondition_failed(self):
        """Submit batch with no requests → PreconditionFailedError."""
        empty = PaymentBatch.objects.create(
            title="Empty",
            status="DRAFT",
            created_by=self.creator,
        )
        with self.assertRaises(PreconditionFailedError):
            services.submit_batch(empty.id, self.creator.id)


# -----------------------------------------------------------------------------
# 4. IDEMPOTENCY REPLAY AT SERVICE LAYER
# Same key twice → no duplicate side effects; second call returns same result.
# -----------------------------------------------------------------------------


class IdempotencyReplayServiceTests(TestCase):
    """Idempotency replay at service layer: no duplicate ApprovalRecord/audit."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="idem_creator",
            password="testpass123",
            display_name="Idem Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="idem_approver",
            password="testpass123",
            display_name="Idem Approver",
            role="APPROVER",
        )
        self.admin = User.objects.create_user(
            username="idem_admin",
            password="testpass123",
            display_name="Idem Admin",
            role="ADMIN",
        )
        self.batch = PaymentBatch.objects.create(
            title="Idem Batch",
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

    def test_approve_replay_same_key_no_duplicate_approval_record(self):
        """Approve twice with same idempotency key → one ApprovalRecord."""
        key = "idem-approve-replay"
        r1 = services.approve_request(
            self.req.id, self.approver.id, comment="OK", idempotency_key=key
        )
        r2 = services.approve_request(
            self.req.id, self.approver.id, comment="Again", idempotency_key=key
        )
        self.assertEqual(r1.id, r2.id)
        self.assertEqual(
            ApprovalRecord.objects.filter(payment_request=self.req).count(), 1
        )

    def test_approve_replay_same_key_replay_flag_set(self):
        """Replay with same key sets _idempotency_replay to [True]."""
        key = "idem-approve-replay-flag"
        replay = []
        services.approve_request(
            self.req.id,
            self.approver.id,
            comment="OK",
            idempotency_key=key,
            _idempotency_replay=replay,
        )
        self.assertEqual(replay, [])
        replay2 = []
        services.approve_request(
            self.req.id,
            self.approver.id,
            comment="Again",
            idempotency_key=key,
            _idempotency_replay=replay2,
        )
        self.assertEqual(replay2, [True])

    def test_reject_replay_same_key_no_duplicate_approval_record(self):
        """Reject twice with same idempotency key → one ApprovalRecord."""
        key = "idem-reject-replay"
        services.reject_request(
            self.req.id, self.approver.id, comment="No", idempotency_key=key
        )
        services.reject_request(
            self.req.id, self.approver.id, comment="Again", idempotency_key=key
        )
        self.assertEqual(
            ApprovalRecord.objects.filter(payment_request=self.req).count(), 1
        )

    def test_mark_paid_replay_same_key_no_duplicate_paid_audit(self):
        """Mark paid twice with same key → one REQUEST_PAID audit."""
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="idem-mp-approve"
        )
        self.req.refresh_from_db()
        key = "idem-markpaid-replay"
        services.mark_paid(self.req.id, self.admin.id, idempotency_key=key)
        services.mark_paid(self.req.id, self.admin.id, idempotency_key=key)
        paid_audits = AuditLog.objects.filter(
            entity_id=self.req.id, event_type="REQUEST_PAID"
        )
        self.assertEqual(paid_audits.count(), 1)

    def test_submit_already_submitted_batch_raises_invalid_state(self):
        """Submit batch when already PROCESSING → InvalidStateError."""
        with self.assertRaises(InvalidStateError):
            services.submit_batch(self.batch.id, self.creator.id)

    def test_cancel_already_cancelled_batch_returns_same_batch(self):
        """Cancel batch when already CANCELLED → idempotent return."""
        from django.utils import timezone

        cancel_batch = PaymentBatch.objects.create(
            title="Cancel Idem",
            status="DRAFT",
            created_by=self.creator,
        )
        # Set to CANCELLED with submitted_at/completed_at so constraint holds
        now = timezone.now()
        PaymentBatch.objects.filter(id=cancel_batch.id).update(
            status="CANCELLED",
            submitted_at=now,
            completed_at=now,
        )
        cancel_batch.refresh_from_db()
        batch_again = services.cancel_batch(cancel_batch.id, self.creator.id)
        self.assertEqual(batch_again.id, cancel_batch.id)
        self.assertEqual(batch_again.status, "CANCELLED")


# -----------------------------------------------------------------------------
# 5. PERMISSION VIOLATIONS AT SERVICE LAYER
# Non-creator add_request; non-approver approve; non-admin mark_paid; etc.
# -----------------------------------------------------------------------------


class PermissionViolationServiceTests(TestCase):
    """PermissionDeniedError when wrong role calls mutation."""

    def setUp(self):
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

    def test_add_request_non_creator_raises_permission_denied(self):
        """Only batch creator can add requests (approver cannot)."""
        with self.assertRaises(PermissionDeniedError):
            services.add_request(
                self.batch.id,
                self.approver.id,
                amount=Decimal("50"),
                currency="USD",
                beneficiary_name="X",
                beneficiary_account="A",
                purpose="P",
                idempotency_key="perm-add-req",
            )

    def test_approve_request_creator_raises_permission_denied(self):
        """Only APPROVER/ADMIN can approve (creator cannot)."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        with self.assertRaises(PermissionDeniedError):
            services.approve_request(
                self.req.id,
                self.creator.id,
                comment="OK",
                idempotency_key="perm-app-creator",
            )

    def test_reject_request_creator_raises_permission_denied(self):
        """Only APPROVER/ADMIN can reject."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        with self.assertRaises(PermissionDeniedError):
            services.reject_request(
                self.req.id,
                self.creator.id,
                comment="No",
                idempotency_key="perm-rej-creator",
            )

    def test_mark_paid_viewer_raises_permission_denied(self):
        """Only CREATOR/APPROVER/ADMIN can mark paid (viewer cannot)."""
        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        services.approve_request(
            self.req.id, self.approver.id, idempotency_key="perm-mp-approve"
        )
        self.req.refresh_from_db()
        with self.assertRaises(PermissionDeniedError):
            services.mark_paid(
                self.req.id, self.viewer.id, idempotency_key="perm-mp-viewer"
            )

    def test_submit_batch_non_creator_raises_permission_denied(self):
        """Only batch creator can submit."""
        with self.assertRaises(PermissionDeniedError):
            services.submit_batch(self.batch.id, self.approver.id)

    def test_cancel_batch_non_creator_raises_permission_denied(self):
        """Only batch creator can cancel."""
        with self.assertRaises(PermissionDeniedError):
            services.cancel_batch(self.batch.id, self.approver.id)

    def test_update_request_non_creator_raises_permission_denied(self):
        """Only batch creator can update request (approver cannot)."""
        with self.assertRaises(PermissionDeniedError):
            services.update_request(
                self.req.id,
                self.batch.id,
                self.approver.id,
                amount=Decimal("99"),
            )


# -----------------------------------------------------------------------------
# 6. CONFLICT / DOMAIN ERROR BRANCHES
# NotFoundError, ValidationError, duplicate prevention, etc.
# -----------------------------------------------------------------------------


class ServiceConflictAndValidationTests(TestCase):
    """NotFoundError, ValidationError, and other domain error branches."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="conf_creator",
            password="testpass123",
            display_name="Conf Creator",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="conf_approver",
            password="testpass123",
            display_name="Conf Approver",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="Conf Batch",
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

    def test_create_batch_empty_title_raises_validation_error(self):
        """create_batch with empty title → ValidationError."""
        with self.assertRaises(ValidationError):
            services.create_batch(self.creator.id, "")

    def test_create_batch_whitespace_title_raises_validation_error(self):
        """create_batch with whitespace-only title → ValidationError."""
        with self.assertRaises(ValidationError):
            services.create_batch(self.creator.id, "   ")

    def test_create_batch_nonexistent_creator_raises_not_found(self):
        """create_batch with non-existent creator_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.create_batch(uuid.uuid4(), "Title")

    def test_add_request_batch_not_found_raises_not_found(self):
        """add_request with non-existent batch_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.add_request(
                uuid.uuid4(),
                self.creator.id,
                amount=Decimal("50"),
                currency="USD",
                beneficiary_name="X",
                beneficiary_account="A",
                purpose="P",
                idempotency_key="add-404",
            )

    def test_add_request_negative_amount_raises_validation_error(self):
        """add_request with amount <= 0 → ValidationError."""
        with self.assertRaises(ValidationError):
            services.add_request(
                self.batch.id,
                self.creator.id,
                amount=Decimal("0"),
                currency="USD",
                beneficiary_name="X",
                beneficiary_account="A",
                purpose="P",
                idempotency_key="add-neg",
            )

    def test_update_request_not_found_raises_not_found(self):
        """update_request with non-existent request_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.update_request(
                uuid.uuid4(),
                self.batch.id,
                self.creator.id,
                amount=Decimal("99"),
            )

    def test_update_request_wrong_batch_raises_not_found(self):
        """update_request with request not in given batch → NotFoundError."""
        other_batch = PaymentBatch.objects.create(
            title="Other",
            status="DRAFT",
            created_by=self.creator,
        )
        with self.assertRaises(NotFoundError):
            services.update_request(
                self.req.id,
                other_batch.id,
                self.creator.id,
                amount=Decimal("99"),
            )

    def test_approve_request_not_found_raises_not_found(self):
        """approve_request with non-existent request_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.approve_request(
                uuid.uuid4(), self.approver.id, idempotency_key="app-404"
            )

    def test_reject_request_not_found_raises_not_found(self):
        """reject_request with non-existent request_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.reject_request(
                uuid.uuid4(), self.approver.id, idempotency_key="rej-404"
            )

    def test_mark_paid_request_not_found_raises_not_found(self):
        """mark_paid with non-existent request_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.mark_paid(uuid.uuid4(), self.creator.id, idempotency_key="mp-404")

    def test_upload_soa_no_file_raises_validation_error(self):
        """upload_soa with no file → ValidationError."""
        with self.assertRaises(ValidationError):
            services.upload_soa(
                self.batch.id,
                self.req.id,
                self.creator.id,
                None,
            )

    def test_upload_soa_request_not_draft_raises_invalid_state(self):
        """upload_soa when request is not DRAFT → InvalidStateError."""
        from django.core.files.base import ContentFile

        services.submit_batch(self.batch.id, self.creator.id)
        self.req.refresh_from_db()
        with self.assertRaises(InvalidStateError):
            services.upload_soa(
                self.batch.id,
                self.req.id,
                self.creator.id,
                ContentFile(b"fake"),
            )


# -----------------------------------------------------------------------------
# 7. SOA GENERATION TRIGGER PATH (first-time success)
# Covered in BatchCompletionLogicTests; one more for already-generated skip.
# -----------------------------------------------------------------------------
# See test_generate_soa_for_batch_already_generated_returns_empty above.

# -----------------------------------------------------------------------------
# 8. REJECT IDEMPOTENT WHEN ALREADY REJECTED
# -----------------------------------------------------------------------------


class RejectIdempotentWhenAlreadyRejectedTests(TestCase):
    """Reject when already REJECTED returns same request (idempotent)."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="rej_idem_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="rej_idem_approver",
            password="testpass123",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="Rej Idem Batch",
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
        services.reject_request(
            self.req.id, self.approver.id, comment="No", idempotency_key="rej-first"
        )
        self.req.refresh_from_db()

    def test_reject_already_rejected_returns_same_request(self):
        """Reject when status already REJECTED → return request (idempotent)."""
        r = services.reject_request(
            self.req.id, self.approver.id, comment="Again", idempotency_key="rej-second"
        )
        self.assertEqual(r.id, self.req.id)
        self.assertEqual(r.status, "REJECTED")


# -----------------------------------------------------------------------------
# STEP 5D — Surgical coverage for services.py missing blocks
# Targets: update_request (436-500), cancel_batch (686-731), submit (530-591),
# approve (789-818), reject (932-982), mark_paid (1066-1092), add_request,
# upload_soa (1205-1267).
# -----------------------------------------------------------------------------


class UpdateRequestFullPathTests(TestCase):
    """update_request: success path with audit, closed batch, creator not found."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="ur_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="UR Batch",
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

    def test_update_request_success_all_fields_creates_audit(self):
        """update_request with all fields → audit REQUEST_UPDATED."""
        updated = services.update_request(
            self.req.id,
            self.batch.id,
            self.creator.id,
            amount=Decimal("200"),
            currency="EUR",
            beneficiary_name="NewBen",
            beneficiary_account="NEWACC",
            purpose="New purpose",
        )
        self.assertEqual(updated.amount, Decimal("200"))
        self.assertEqual(updated.currency, "EUR")
        self.assertEqual(updated.beneficiary_name, "NewBen")
        self.assertEqual(updated.beneficiary_account, "NEWACC")
        self.assertEqual(updated.purpose, "New purpose")
        self.assertEqual(
            AuditLog.objects.filter(
                entity_id=self.req.id, event_type="REQUEST_UPDATED"
            ).count(),
            1,
        )

    def test_update_request_closed_batch_raises_invalid_state(self):
        """update_request when batch is closed (e.g. CANCELLED) → InvalidStateError."""
        from django.utils import timezone

        PaymentBatch.objects.filter(id=self.batch.id).update(
            status="CANCELLED",
            submitted_at=timezone.now(),
            completed_at=timezone.now(),
        )
        self.batch.refresh_from_db()
        # Request still DRAFT; update_request hits is_closed_batch(batch.status)
        with self.assertRaises(InvalidStateError) as ctx:
            services.update_request(
                self.req.id, self.batch.id, self.creator.id, amount=Decimal("99")
            )
        self.assertIn("closed batch", str(ctx.exception.message))

    def test_update_request_creator_not_found_raises_not_found(self):
        """update_request with non-existent creator_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.update_request(
                self.req.id,
                self.batch.id,
                uuid.uuid4(),
                amount=Decimal("99"),
            )


class CancelBatchMissingBranchesTests(TestCase):
    """cancel_batch: User/Batch DoesNotExist, success path with audit."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="cb_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="CB Batch",
            status="DRAFT",
            created_by=self.creator,
        )

    def test_cancel_batch_user_not_found_raises_not_found(self):
        """cancel_batch with non-existent creator_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.cancel_batch(self.batch.id, uuid.uuid4())

    def test_cancel_batch_batch_not_found_raises_not_found(self):
        """cancel_batch with non-existent batch_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.cancel_batch(uuid.uuid4(), self.creator.id)

    def test_cancel_batch_success_creates_audit(self):
        """cancel_batch on DRAFT → status CANCELLED and BATCH_CANCELLED audit."""
        batch = services.cancel_batch(self.batch.id, self.creator.id)
        self.assertEqual(batch.status, "CANCELLED")
        self.assertIsNotNone(batch.completed_at)
        self.assertEqual(
            AuditLog.objects.filter(
                entity_id=self.batch.id, event_type="BATCH_CANCELLED"
            ).count(),
            1,
        )


class SubmitBatchMissingBranchesTests(TestCase):
    """submit_batch: idempotent when SUBMITTED; PreconditionFailed for ledger/legacy."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="sb_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="SB Batch",
            status="DRAFT",
            created_by=self.creator,
        )

    def test_submit_batch_idempotent_when_already_submitted_returns_batch(self):
        """submit_batch when already SUBMITTED → returns batch (idempotent)."""
        from django.utils import timezone

        PaymentBatch.objects.filter(id=self.batch.id).update(
            status="SUBMITTED",
            submitted_at=timezone.now(),
        )
        self.batch.refresh_from_db()
        result = services.submit_batch(self.batch.id, self.creator.id)
        self.assertEqual(result.id, self.batch.id)
        self.assertEqual(result.status, "SUBMITTED")

    def test_submit_batch_legacy_request_missing_required_fields_raises_precondition(
        self,
    ):
        """submit_batch with empty beneficiary_name → PreconditionFailedError."""
        PaymentRequest.objects.create(
            batch=self.batch,
            status="DRAFT",
            currency="USD",
            created_by=self.creator,
            beneficiary_name="",
            beneficiary_account="ACC",
            purpose="P",
            amount=Decimal("100"),
        )
        with self.assertRaises(PreconditionFailedError) as ctx:
            services.submit_batch(self.batch.id, self.creator.id)
        self.assertIn("missing required fields", str(ctx.exception.message))


class ApproveRequestMissingBranchesTests(TestCase):
    """approve_request: existing ApprovalRecord (idempotent), IntegrityError race."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="ap_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="ap_approver",
            password="testpass123",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="AP Batch",
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

    def test_approve_when_approval_record_exists_returns_request_idempotent(self):
        """ApprovalRecord exists → approve returns request (idempotent)."""
        ApprovalRecord.objects.create(
            payment_request=self.req,
            approver=self.approver,
            decision="APPROVED",
        )
        r = services.approve_request(
            self.req.id,
            self.approver.id,
            comment="OK",
            idempotency_key="ap-existing-rec",
        )
        self.assertEqual(r.id, self.req.id)
        self.assertEqual(
            ApprovalRecord.objects.filter(payment_request=self.req).count(), 1
        )

    def test_approve_integrity_error_race_returns_request_idempotent(self):
        """Race: ApprovalRecord create raises IntegrityError → return request."""
        with patch(
            "apps.payments.services.ApprovalRecord.objects.create",
            side_effect=IntegrityError("duplicate"),
        ):
            r = services.approve_request(
                self.req.id,
                self.approver.id,
                comment="OK",
                idempotency_key="ap-integrity-race",
            )
        self.assertEqual(r.id, self.req.id)


class RejectRequestMissingBranchesTests(TestCase):
    """reject_request: User DoesNotExist, ApprovalRecord exists, IntegrityError."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="rj_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="rj_approver",
            password="testpass123",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="RJ Batch",
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

    def test_reject_user_not_found_raises_not_found(self):
        """reject_request with non-existent approver_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.reject_request(
                self.req.id, uuid.uuid4(), comment="No", idempotency_key="rj-404"
            )

    def test_reject_when_approval_record_exists_returns_request_idempotent(self):
        """ApprovalRecord exists (PENDING_APPROVAL) → reject returns request."""
        ApprovalRecord.objects.create(
            payment_request=self.req,
            approver=self.approver,
            decision="REJECTED",
        )
        # Existing record; reject_request returns request idempotently
        r = services.reject_request(
            self.req.id,
            self.approver.id,
            comment="No",
            idempotency_key="rj-existing-rec",
        )
        self.assertEqual(r.id, self.req.id)

    def test_reject_integrity_error_race_returns_request_idempotent(self):
        """Race: ApprovalRecord create raises IntegrityError → return request."""
        with patch(
            "apps.payments.services.ApprovalRecord.objects.create",
            side_effect=IntegrityError("duplicate"),
        ):
            r = services.reject_request(
                self.req.id,
                self.approver.id,
                comment="No",
                idempotency_key="rj-integrity-race",
            )
        self.assertEqual(r.id, self.req.id)


class MarkPaidMissingBranchesTests(TestCase):
    """mark_paid: User DoesNotExist, already PAID idempotent return."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="mp_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="mp_approver",
            password="testpass123",
            role="APPROVER",
        )
        self.admin = User.objects.create_user(
            username="mp_admin",
            password="testpass123",
            role="ADMIN",
        )
        self.batch = PaymentBatch.objects.create(
            title="MP Batch",
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
            self.req.id, self.approver.id, idempotency_key="mp-app"
        )
        self.req.refresh_from_db()

    def test_mark_paid_user_not_found_raises_not_found(self):
        """mark_paid with non-existent actor_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.mark_paid(self.req.id, uuid.uuid4(), idempotency_key="mp-404")

    def test_mark_paid_already_paid_idempotent_returns_same_request(self):
        """mark_paid when status already PAID → return request (idempotent)."""
        services.mark_paid(self.req.id, self.admin.id, idempotency_key="mp-first")
        self.req.refresh_from_db()
        r = services.mark_paid(self.req.id, self.admin.id, idempotency_key="mp-second")
        self.assertEqual(r.id, self.req.id)
        self.assertEqual(r.status, "PAID")


class AddRequestMissingBranchesTests(TestCase):
    """add_request: creator not found, idempotency duplicate return, batch not DRAFT."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="ar_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.batch = PaymentBatch.objects.create(
            title="AR Batch",
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

    def test_add_request_creator_not_found_raises_not_found(self):
        """add_request with non-existent creator_id → NotFoundError."""
        import uuid

        with self.assertRaises(NotFoundError):
            services.add_request(
                self.batch.id,
                uuid.uuid4(),
                amount=Decimal("50"),
                currency="USD",
                beneficiary_name="X",
                beneficiary_account="A",
                purpose="P",
                idempotency_key="ar-creator-404",
            )

    def test_add_request_idempotency_duplicate_returns_existing_request(self):
        """add_request twice with same idempotency_key → second returns same request."""
        r1 = services.add_request(
            self.batch.id,
            self.creator.id,
            amount=Decimal("50"),
            currency="USD",
            beneficiary_name="X",
            beneficiary_account="A",
            purpose="P",
            idempotency_key="ar-idem-dup",
        )
        r2 = services.add_request(
            self.batch.id,
            self.creator.id,
            amount=Decimal("99"),
            currency="USD",
            beneficiary_name="Y",
            beneficiary_account="B",
            purpose="Q",
            idempotency_key="ar-idem-dup",
        )
        self.assertEqual(r1.id, r2.id)
        self.assertEqual(r2.amount, Decimal("50"))

    def test_add_request_batch_not_draft_raises_invalid_state(self):
        """add_request when batch is not DRAFT → InvalidStateError."""
        # Batch has one request so submit_batch succeeds
        services.submit_batch(self.batch.id, self.creator.id)
        self.batch.refresh_from_db()
        with self.assertRaises(InvalidStateError) as ctx:
            services.add_request(
                self.batch.id,
                self.creator.id,
                amount=Decimal("50"),
                currency="USD",
                beneficiary_name="X",
                beneficiary_account="A",
                purpose="P",
                idempotency_key="ar-not-draft",
            )
        self.assertIn("Cannot add request to batch", str(ctx.exception.message))


class UploadSoaMissingBranchesTests(TestCase):
    """upload_soa: creator not found, wrong batch, permission, closed batch, success."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="soa_creator",
            password="testpass123",
            role="CREATOR",
        )
        self.approver = User.objects.create_user(
            username="soa_approver",
            password="testpass123",
            role="APPROVER",
        )
        self.batch = PaymentBatch.objects.create(
            title="SOA Batch",
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

    def test_upload_soa_creator_not_found_raises_not_found(self):
        """upload_soa with non-existent creator_id → NotFoundError."""
        import uuid

        from django.core.files.base import ContentFile

        with self.assertRaises(NotFoundError):
            services.upload_soa(
                self.batch.id,
                self.req.id,
                uuid.uuid4(),
                ContentFile(b"fake"),
            )

    def test_upload_soa_wrong_batch_raises_not_found(self):
        """upload_soa with request not in given batch → NotFoundError."""
        from django.core.files.base import ContentFile

        other_batch = PaymentBatch.objects.create(
            title="Other",
            status="DRAFT",
            created_by=self.creator,
        )
        with self.assertRaises(NotFoundError):
            services.upload_soa(
                other_batch.id,
                self.req.id,
                self.creator.id,
                ContentFile(b"fake"),
            )

    def test_upload_soa_non_creator_raises_permission_denied(self):
        """upload_soa by non-creator (approver) → PermissionDeniedError."""
        from django.core.files.base import ContentFile

        with self.assertRaises(PermissionDeniedError):
            services.upload_soa(
                self.batch.id,
                self.req.id,
                self.approver.id,
                ContentFile(b"fake"),
            )

    def test_upload_soa_closed_batch_raises_invalid_state(self):
        """upload_soa when batch is closed → InvalidStateError."""
        from django.core.files.base import ContentFile
        from django.utils import timezone

        PaymentBatch.objects.filter(id=self.batch.id).update(
            status="CANCELLED",
            submitted_at=timezone.now(),
            completed_at=timezone.now(),
        )
        self.batch.refresh_from_db()
        with self.assertRaises(InvalidStateError) as ctx:
            services.upload_soa(
                self.batch.id,
                self.req.id,
                self.creator.id,
                ContentFile(b"fake"),
            )
        self.assertIn("closed batch", str(ctx.exception.message))

    def test_upload_soa_success_creates_soa_version_and_audit(self):
        """upload_soa with file → SOAVersion created and SOA_UPLOADED audit."""
        from django.core.files.base import ContentFile

        from apps.payments.models import SOAVersion

        soa = services.upload_soa(
            self.batch.id,
            self.req.id,
            self.creator.id,
            ContentFile(b"fake pdf content", name="doc.pdf"),
        )
        self.assertIsNotNone(soa.id)
        self.assertEqual(soa.payment_request_id, self.req.id)
        self.assertEqual(soa.version_number, 1)
        self.assertEqual(soa.source, SOAVersion.SOURCE_UPLOAD)
        self.assertEqual(
            AuditLog.objects.filter(
                entity_id=soa.id, event_type="SOA_UPLOADED"
            ).count(),
            1,
        )
