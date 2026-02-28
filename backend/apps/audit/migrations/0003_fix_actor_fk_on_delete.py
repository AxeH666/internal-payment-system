from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0002_alter_auditlog_options"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE audit_logs DROP CONSTRAINT audit_logs_actor_id_303d1495_fk_users_id;",
                "ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_actor_id_303d1495_fk_users_id FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;",
            ],
            reverse_sql=[
                "ALTER TABLE audit_logs DROP CONSTRAINT audit_logs_actor_id_303d1495_fk_users_id;",
                "ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_actor_id_303d1495_fk_users_id FOREIGN KEY (actor_id) REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED;",
            ],
        ),
    ]
