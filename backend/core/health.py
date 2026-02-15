from django.http import JsonResponse
from django.db import connection


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse(
            {
                "status": "ok",
                "database": "connected",
                "architecture_version": "v0.1.0",
            },
            status=200,
        )
    except Exception:
        return JsonResponse(
            {
                "status": "unhealthy",
                "database": "disconnected",
                "architecture_version": "v0.1.0",
            },
            status=503,
        )
