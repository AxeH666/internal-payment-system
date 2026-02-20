# Add ADMIN role to valid_role constraint.
# Requires: users table must exist (created by 0001_initial).
# Depends on users.0001_initial to ensure User table exists before we alter constraint.

from django.db import migrations


def add_admin_role_constraint(apps, schema_editor):
    """Replace valid_role constraint to include ADMIN."""
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_role;")
        cursor.execute(
            "ALTER TABLE users ADD CONSTRAINT valid_role "
            "CHECK (role IN ('CREATOR', 'APPROVER', 'VIEWER', 'ADMIN'));"
        )


def reverse_add_admin_role_constraint(apps, schema_editor):
    """Restore original 3-role constraint."""
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_role;")
        cursor.execute(
            "ALTER TABLE users ADD CONSTRAINT valid_role "
            "CHECK (role IN ('CREATOR', 'APPROVER', 'VIEWER'));"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            add_admin_role_constraint, reverse_add_admin_role_constraint
        ),
    ]
