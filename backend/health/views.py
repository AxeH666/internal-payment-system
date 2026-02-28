from django.db import connection
from django.core.cache import caches
from django.apps import apps
from django.db.migrations.executor import MigrationExecutor
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response


class LiveView(APIView):
    """Liveness probe: process is running. No DB or external deps."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "alive"})


class ReadyView(APIView):
    """Readiness probe: DB, cache, migrations, idempotency table."""

    permission_classes = [AllowAny]

    def get(self, request):
        return self._run_checks()

    def _run_checks(self):

        checks = {}

        # DB check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        # Migration consistency check
        try:
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            checks["migrations"] = "ok" if not plan else "pending"
        except Exception:
            checks["migrations"] = "error"

        # Cache check
        try:
            cache = caches["default"]
            cache.set("health_check", "ok", timeout=5)
            if cache.get("health_check") == "ok":
                checks["cache"] = "ok"
            else:
                checks["cache"] = "error"
        except Exception:
            checks["cache"] = "error"

        # Idempotency table accessibility
        try:
            IdempotencyKey = apps.get_model("payments", "IdempotencyKey")
            IdempotencyKey.objects.exists()
            checks["idempotency_table"] = "ok"
        except Exception:
            checks["idempotency_table"] = "error"

        overall = "ready" if all(v == "ok" for v in checks.values()) else "not_ready"

        return Response({"status": overall, "checks": checks})
