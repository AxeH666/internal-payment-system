"""
URL routing for audit log endpoints.
"""

from django.urls import path
from apps.audit import views

app_name = "audit"

urlpatterns = [
    path("", views.query_audit_log, name="query-audit-log"),
    path(
        "logs", views.query_audit_log, name="query-audit-logs"
    ),  # Alias for test compatibility
]
