"""
URL routing for ledger endpoints.
"""

from django.urls import path
from apps.ledger import views

app_name = "ledger"

urlpatterns = [
    # Clients
    path("clients", views.list_or_create_clients, name="list-or-create-clients"),
    path("clients/<uuid:clientId>", views.update_client, name="update-client"),
    # Sites
    path("sites", views.list_or_create_sites, name="list-or-create-sites"),
    path("sites/<uuid:siteId>", views.update_site, name="update-site"),
    # Vendors
    path("vendors", views.list_or_create_vendors, name="list-or-create-vendors"),
    path("vendors/<uuid:vendorId>", views.update_vendor, name="update-vendor"),
    # Subcontractors
    path(
        "subcontractors",
        views.list_or_create_subcontractors,
        name="list-or-create-subcontractors",
    ),
    path(
        "subcontractors/<uuid:subcontractorId>",
        views.update_subcontractor,
        name="update-subcontractor",
    ),
    # Vendor Types
    path("vendor-types", views.list_vendor_types, name="list-vendor-types"),
    # Subcontractor Scopes
    path("scopes", views.list_subcontractor_scopes, name="list-scopes"),
]
