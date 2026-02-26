from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("health.urls")),
    # API v1 (per docs/04_API_CONTRACT.md base path: /api/v1)
    path("api/v1/auth/", include("apps.auth.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/ledger/", include("apps.ledger.urls")),
    # Payments endpoints are defined directly under /api/v1 (e.g., /api/v1/batches)
    path("api/v1/", include("apps.payments.urls")),
]
