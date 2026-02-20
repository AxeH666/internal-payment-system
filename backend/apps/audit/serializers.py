"""
Serializers for AuditLog model.
"""

from rest_framework import serializers
from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog."""

    id = serializers.UUIDField(read_only=True)
    eventType = serializers.CharField(source="event_type", read_only=True)
    actorId = serializers.UUIDField(source="actor_id", read_only=True, allow_null=True)
    entityType = serializers.CharField(source="entity_type", read_only=True)
    entityId = serializers.UUIDField(source="entity_id", read_only=True)
    previousState = serializers.JSONField(
        source="previous_state", read_only=True, allow_null=True
    )
    newState = serializers.JSONField(
        source="new_state", read_only=True, allow_null=True
    )
    occurredAt = serializers.DateTimeField(source="occurred_at", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "eventType",
            "actorId",
            "entityType",
            "entityId",
            "previousState",
            "newState",
            "occurredAt",
        ]
