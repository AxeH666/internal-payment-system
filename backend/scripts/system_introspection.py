"""
SYSTEM INTROSPECTION SCRIPT
Reveals actual DB names, constraints, roles, and installed models.
"""

import os
import sys

# CRITICAL FIX: Add /app to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# CRITICAL FIX: Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from django.conf import settings
from django.db import connection
from django.apps import apps


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def show_database_info():
    print_header("DATABASE INFO")

    db = settings.DATABASES["default"]

    print("ENGINE:", db.get("ENGINE"))
    print("NAME:", db.get("NAME"))
    print("USER:", db.get("USER"))
    print("HOST:", db.get("HOST"))
    print("PORT:", db.get("PORT"))


def show_tables():
    print_header("DATABASE TABLES")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname='public'
            ORDER BY tablename;
        """)

        tables = cursor.fetchall()

        for t in tables:
            print(t[0])


def show_constraints():
    print_header("DATABASE CONSTRAINTS")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'public'
            ORDER BY conname;
        """)

        constraints = cursor.fetchall()

        for name, definition in constraints:
            print(f"{name}: {definition}")


def show_user_roles():
    print_header("USER ROLES IN DB")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT role FROM users;
        """)

        roles = cursor.fetchall()

        for r in roles:
            print("ROLE:", r[0])


def show_installed_apps():
    print_header("INSTALLED DJANGO APPS")

    for app in settings.INSTALLED_APPS:
        print(app)


def show_models():
    print_header("REGISTERED MODELS")

    for model in apps.get_models():
        print(model._meta.label)


def main():
    print_header("SYSTEM INTROSPECTION STARTED")

    show_database_info()
    show_tables()
    show_constraints()
    show_user_roles()
    show_installed_apps()
    show_models()

    print_header("INTROSPECTION COMPLETE")


if __name__ == "__main__":
    main()
