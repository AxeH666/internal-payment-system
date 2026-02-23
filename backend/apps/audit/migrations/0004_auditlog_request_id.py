# Phase 3.1 — Structured Logging: attach request_id to AuditLog for correlation.
#
# Safety: null=True, blank=True — no NOT NULL constraint. Existing rows remain
# readable and get request_id=NULL. Index on request_id can be added later if
# querying by request_id becomes necessary.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0003_fix_actor_fk_on_delete"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="request_id",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
