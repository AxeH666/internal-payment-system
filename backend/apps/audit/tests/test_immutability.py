import pytest

from apps.audit.models import AuditLog


@pytest.mark.django_db
def test_audit_log_bulk_update_blocked():
    log = AuditLog.objects.create(
        event_type="TEST",
        entity_type="X",
        entity_id="00000000-0000-0000-0000-000000000000",
    )

    with pytest.raises(ValueError):
        AuditLog.objects.filter(pk=log.pk).update(event_type="HACK")


@pytest.mark.django_db
def test_audit_log_bulk_delete_blocked():
    log = AuditLog.objects.create(
        event_type="TEST",
        entity_type="X",
        entity_id="00000000-0000-0000-0000-000000000000",
    )

    with pytest.raises(ValueError):
        AuditLog.objects.filter(pk=log.pk).delete()
