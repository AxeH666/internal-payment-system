"""
URL routing for payment endpoints.
"""

from django.urls import path
from apps.payments import views

app_name = "payments"

urlpatterns = [
    # Batch endpoints
    path(
        "batches", views.create_or_list_batches, name="create-or-list-batches"
    ),  # POST, GET
    path("batches/<uuid:batchId>", views.get_batch, name="get-batch"),
    path("batches/<uuid:batchId>/submit", views.submit_batch, name="submit-batch"),
    path("batches/<uuid:batchId>/cancel", views.cancel_batch, name="cancel-batch"),
    # Request endpoints (nested under batch)
    path(
        "batches/<uuid:batchId>/requests", views.add_request, name="add-request"
    ),  # POST
    path(
        "batches/<uuid:batchId>/requests/<uuid:requestId>",
        views.get_or_update_request,
        name="get-or-update-request",
    ),  # GET, PATCH
    # Request endpoints (standalone)
    path("requests", views.list_pending_requests, name="list-pending-requests"),
    path("requests/<uuid:requestId>", views.get_request, name="get-request"),  # GET
    path(
        "requests/<uuid:requestId>/approve",
        views.approve_request,
        name="approve-request",
    ),
    path(
        "requests/<uuid:requestId>/reject", views.reject_request, name="reject-request"
    ),
    path("requests/<uuid:requestId>/mark-paid", views.mark_paid, name="mark-paid"),
    # SOA endpoints
    path(
        "batches/<uuid:batchId>/requests/<uuid:requestId>/soa",
        views.upload_or_list_soa,
        name="upload-or-list-soa",
    ),  # POST, GET
    path(
        "batches/<uuid:batchId>/requests/<uuid:requestId>/soa/<uuid:versionId>",
        views.get_soa_document,
        name="get-soa-document",
    ),
    path(
        (
            "batches/<uuid:batchId>/requests/<uuid:requestId>/soa/<uuid:versionId>/"
            "download"
        ),
        views.download_soa_document,
        name="download-soa-document",
    ),
    # SOA export (Phase 3 - versioned export)
    path(
        "batches/<uuid:batchId>/soa-export",
        views.export_batch_soa,
        name="export-batch-soa",
    ),
]
