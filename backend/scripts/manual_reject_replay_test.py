#!/usr/bin/env python
"""
Manual reject replay test — 2.3.3.I.
Run: scripts/manual_reject_replay_test.py via manage.py shell (or docker exec).
"""

from apps.users.models import User
from apps.payments.models import ApprovalRecord
from apps.audit.models import AuditLog
from apps.payments import services

# 1. Create creator and approver
creator = User.objects.create_user(
    username="reject_replay_creator",
    password="testpass123",
    display_name="Reject Replay Creator",
    role="CREATOR",
)
approver = User.objects.create_user(
    username="reject_replay_approver",
    password="testpass123",
    display_name="Reject Replay Approver",
    role="APPROVER",
)

# 2. Create batch and request
batch = services.create_batch(creator.id, "Reject Replay Batch")
req = services.add_request(
    batch.id,
    creator.id,
    amount=50,
    currency="USD",
    beneficiary_name="Test",
    beneficiary_account="ACC",
    purpose="Test",
    idempotency_key="reject-create-key",
)

# 3. Submit batch so request is PENDING_APPROVAL
services.submit_batch(batch.id, creator.id)
req.refresh_from_db()
assert req.status == "PENDING_APPROVAL", f"Expected PENDING_APPROVAL got {req.status}"

# 4. First reject with key
idem_key = "reject-replay-key-456"
r1 = services.reject_request(
    req.id, approver.id, comment="First reject", idempotency_key=idem_key
)
print(f"First reject: request_id={r1.id} status={r1.status}")

# 5. Second reject with same key (replay)
r2 = services.reject_request(
    req.id, approver.id, comment="Replay", idempotency_key=idem_key
)
print(f"Second reject (replay): request_id={r2.id} status={r2.status}")

# 6. Assertions
assert r1.id == r2.id, "Second call must return same request"
assert r2.status == "REJECTED", f"Status must remain REJECTED got {r2.status}"
count = ApprovalRecord.objects.filter(payment_request=req).count()
assert count == 1, f"Exactly one ApprovalRecord expected, got {count}"
reject_audit = AuditLog.objects.filter(entity_id=req.id, event_type="APPROVAL_RECORDED")
assert (
    reject_audit.count() == 1
), f"Exactly one APPROVAL_RECORDED audit expected, got {reject_audit.count()}"
# Ensure new_state has REJECTED
assert any(
    "REJECTED" in str(e.new_state) for e in reject_audit
), "Audit should record REJECTED"

print("OK: One ApprovalRecord, REJECTED, one audit row, replay returned same object.")
