"""
AuditLog model - immutable chronological record of domain events.

Audit logs are append-only. No update or delete operations.
"""

import uuid
from django.db import models


class AuditLog(models.Model):
    """AuditLog model - immutable audit trail."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50)
    actor = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
    )
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    request_id = models.CharField(max_length=64, null=True, blank=True)
    previous_state = models.JSONField(null=True, blank=True)
    new_state = models.JSONField(null=True, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"], name="idx_audit_entity"),
            models.Index(fields=["occurred_at"], name="idx_audit_occurred"),
            models.Index(fields=["actor"], name="idx_audit_actor"),
        ]
        ordering = ["-occurred_at"]

    def __str__(self):
        return (
            f"{self.event_type} - {self.entity_type}:{self.entity_id} at "
            f"{self.occurred_at}"
        )

    def save(self, *args, **kwargs):
        """Override save to prevent updates."""
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError(
                "AuditLog entries are append-only. Updates are not allowed."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion."""
        raise ValueError("AuditLog entries are append-only. Deletions are not allowed.")
