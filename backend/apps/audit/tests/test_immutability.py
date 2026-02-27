from django.contrib.auth import get_user_model
from django.test import TestCase
import uuid

from apps.audit.models import AuditLog


class AuditLogImmutabilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="audit_test_user",
            email="test@example.com",
            password="password123",
        )

        self.log = AuditLog.objects.create(
            event_type="TEST_EVENT",
            actor=self.user,
            entity_type="TestEntity",
            entity_id=uuid.uuid4(),
            request_id="test-request-id",
        )

    def test_bulk_update_is_blocked(self):
        with self.assertRaises(ValueError):
            AuditLog.objects.filter(pk=self.log.pk).update(event_type="MODIFIED")

    def test_bulk_delete_is_blocked(self):
        with self.assertRaises(ValueError):
            AuditLog.objects.filter(pk=self.log.pk).delete()
