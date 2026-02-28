#!/usr/bin/env python
"""
STEP 3 — Manual approval replay test.
Run inside container: python manage.py shell < scripts/manual_approval_replay_test.py
"""

from apps.users.models import User
from apps.payments.models import ApprovalRecord
from apps.audit.models import AuditLog
from apps.payments import services

# 1. Create creator and approver
creator = User.objects.create_user(
    username="replay_creator",
    password="testpass123",
    display_name="Replay Creator",
    role="CREATOR",
)
approver = User.objects.create_user(
    username="replay_approver",
    password="testpass123",
    display_name="Replay Approver",
    role="APPROVER",
)

# 2. Create batch and request
batch = services.create_batch(creator.id, "Replay Test Batch")
req = services.add_request(
    batch.id,
    creator.id,
    amount=100,
    currency="USD",
    beneficiary_name="Test",
    beneficiary_account="ACC",
    purpose="Test",
    idempotency_key="create-key-replay",
)

# 3. Submit batch so request is PENDING_APPROVAL
services.submit_batch(batch.id, creator.id)
req.refresh_from_db()
assert req.status == "PENDING_APPROVAL", f"Expected PENDING_APPROVAL got {req.status}"

# 4. First approval with key
idem_key = "approve-replay-key-123"
r1 = services.approve_request(
    req.id, approver.id, comment="First", idempotency_key=idem_key
)
print(f"First approval: request_id={r1.id} status={r1.status}")

# 5. Second approval with same key (replay)
r2 = services.approve_request(
    req.id, approver.id, comment="Replay", idempotency_key=idem_key
)
print(f"Second approval (replay): request_id={r2.id} status={r2.status}")

# 6. Assertions
assert r1.id == r2.id, "Second call must return same request"
assert r2.status == "APPROVED", f"Status must remain APPROVED got {r2.status}"
count = ApprovalRecord.objects.filter(payment_request=req).count()
assert count == 1, f"Exactly one ApprovalRecord expected, got {count}"
approval_events = AuditLog.objects.filter(
    entity_id=req.id, event_type="APPROVAL_RECORDED"
)
assert (
    approval_events.count() == 1
), f"Exactly one APPROVAL_RECORDED audit expected, got {approval_events.count()}"

print("OK: One ApprovalRecord, APPROVED, one audit row, replay returned same object.")
