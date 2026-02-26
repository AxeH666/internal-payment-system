#!/usr/bin/env python
"""
Manual mark_paid replay test — 2.3.3.J.5.
Run: scripts/manual_mark_paid_replay_test.py via manage.py shell (or docker exec).
"""

from apps.users.models import User
from apps.audit.models import AuditLog
from apps.payments import services

# 1. Create creator and approver
creator = User.objects.create_user(
    username="markpaid_replay_creator",
    password="testpass123",
    display_name="MarkPaid Replay Creator",
    role="CREATOR",
)
approver = User.objects.create_user(
    username="markpaid_replay_approver",
    password="testpass123",
    display_name="MarkPaid Replay Approver",
    role="APPROVER",
)

# 2. Create batch and request
batch = services.create_batch(creator.id, "MarkPaid Replay Batch")
req = services.add_request(
    batch.id,
    creator.id,
    amount=75,
    currency="USD",
    beneficiary_name="Test",
    beneficiary_account="ACC",
    purpose="Test",
    idempotency_key="markpaid-create-key",
)

# 3. Submit batch
services.submit_batch(batch.id, creator.id)
req.refresh_from_db()
assert req.status == "PENDING_APPROVAL", f"Expected PENDING_APPROVAL got {req.status}"

# 4. Approve request
services.approve_request(
    req.id, approver.id, comment="Approve", idempotency_key="markpaid-approve-key"
)
req.refresh_from_db()
assert req.status == "APPROVED", f"Expected APPROVED got {req.status}"

# 5. First mark_paid with key
idem_key = "markpaid-replay-key-789"
r1 = services.mark_paid(req.id, creator.id, idempotency_key=idem_key)
print(f"First mark_paid: request_id={r1.id} status={r1.status}")

# 6. Second mark_paid with same key (replay)
r2 = services.mark_paid(req.id, creator.id, idempotency_key=idem_key)
print(f"Second mark_paid (replay): request_id={r2.id} status={r2.status}")

# 7. Assertions
assert r1.id == r2.id, "Second call must return same request"
assert r2.status == "PAID", f"Status must remain PAID got {r2.status}"
paid_audit = AuditLog.objects.filter(entity_id=req.id, event_type="REQUEST_PAID")
assert (
    paid_audit.count() == 1
), f"Exactly one REQUEST_PAID audit expected, got {paid_audit.count()}"

print("OK: Same object, PAID, one REQUEST_PAID audit, no duplicate transition.")
