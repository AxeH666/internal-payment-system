# Generated migration for AuditLog model
# Audit logs are append-only immutable records of domain events.

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("event_type", models.CharField(max_length=50)),
                ("entity_type", models.CharField(max_length=50)),
                ("entity_id", models.UUIDField()),
                ("previous_state", models.JSONField(blank=True, null=True)),
                ("new_state", models.JSONField(blank=True, null=True)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "audit_logs",
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["entity_type", "entity_id"], name="idx_audit_entity"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["occurred_at"], name="idx_audit_occurred"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["actor"], name="idx_audit_actor"),
        ),
    ]
