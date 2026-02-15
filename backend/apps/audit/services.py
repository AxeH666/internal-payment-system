"""
Audit service - creates immutable audit log entries.

All audit entries are append-only. No updates or deletions.
"""

from apps.audit.models import AuditLog


def create_audit_entry(
    event_type, actor_id, entity_type, entity_id, previous_state=None, new_state=None
):
    """
    Create an audit log entry.

    Args:
        event_type: Event classification (e.g. 'BATCH_CREATED')
        actor_id: User identifier (None for system events)
        entity_type: Type of affected entity (e.g. 'PaymentBatch')
        entity_id: Identifier of affected entity
        previous_state: Serialized state before change (optional)
        new_state: Serialized state after change (optional)

    Returns:
        AuditLog: Created audit log entry
    """
    from apps.users.models import User

    actor = None
    if actor_id:
        try:
            actor = User.objects.get(id=actor_id)
        except User.DoesNotExist:
            # Actor may not exist if user was deleted, but we still log
            pass

    audit_entry = AuditLog.objects.create(
        event_type=event_type,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
    )

    return audit_entry
