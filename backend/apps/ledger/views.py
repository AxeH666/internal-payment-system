"""
Ledger API views.

All mutations flow through service layer.
Admin-only mutations for POST/PATCH.
Read-only for authenticated users.
"""

from django.db import IntegrityError

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from core.permissions import IsAdmin, IsAuthenticatedReadOnly
from core.exceptions import DomainError
from apps.ledger import services
from apps.ledger.models import (
    Client,
    Site,
    VendorType,
    SubcontractorScope,
    Vendor,
    Subcontractor,
)
from apps.ledger.serializers import (
    ClientSerializer,
    SiteSerializer,
    VendorTypeSerializer,
    SubcontractorScopeSerializer,
    VendorSerializer,
    SubcontractorSerializer,
)

# -----------------------------
# Clients
# -----------------------------


@api_view(["GET", "POST"])
def list_or_create_clients(request):
    """GET /api/v1/ledger/clients - List clients (read-only)"""
    """POST /api/v1/ledger/clients - Create client (admin-only)"""
    if request.method == "GET":
        if not IsAuthenticatedReadOnly().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Permission denied",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = Client.objects.filter(is_active=True).order_by("name")
        serializer = ClientSerializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    else:  # POST
        if not IsAdmin().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Only ADMIN can create clients",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        name = request.data.get("name")
        if not name:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Name is required",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = services.create_client(request.user.id, name)
            serializer = ClientSerializer(client)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
        except DomainError:
            raise
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "A client with this name already exists",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def update_client(request, clientId):
    """PATCH /api/v1/ledger/clients/{clientId} - Update client (admin-only)"""
    is_active = request.data.get("isActive")
    if is_active is None:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "isActive is required",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = services.update_client(request.user.id, clientId, is_active=is_active)
        serializer = ClientSerializer(client)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise


# -----------------------------
# Sites
# -----------------------------


@api_view(["GET", "POST"])
def list_or_create_sites(request):
    """GET /api/v1/ledger/sites - List sites (read-only)"""
    """POST /api/v1/ledger/sites - Create site (admin-only)"""
    if request.method == "GET":
        if not IsAuthenticatedReadOnly().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Permission denied",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = (
            Site.objects.filter(is_active=True)
            .select_related("client")
            .order_by("code")
        )
        serializer = SiteSerializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    else:  # POST
        if not IsAdmin().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Only ADMIN can create sites",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        code = request.data.get("code")
        name = request.data.get("name")
        client_id = request.data.get("clientId")

        if not code or not name:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "code and name are required",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If clientId not provided, create or get a default client
        if not client_id:
            from apps.ledger.models import Client

            default_client, _ = Client.objects.get_or_create(
                name="Default Client", defaults={"is_active": True}
            )
            client_id = default_client.id

        try:
            site = services.create_site(request.user.id, code, name, client_id)
            serializer = SiteSerializer(site)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
        except DomainError:
            raise
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "A site with this code already exists",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def update_site(request, siteId):
    """PATCH /api/v1/ledger/sites/{siteId} - Update site (admin-only)"""
    is_active = request.data.get("isActive")
    if is_active is None:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "isActive is required",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        site = services.update_site(request.user.id, siteId, is_active=is_active)
        serializer = SiteSerializer(site)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise


# -----------------------------
# Vendors
# -----------------------------


@api_view(["GET", "POST"])
def list_or_create_vendors(request):
    """GET /api/v1/ledger/vendors - List vendors (read-only)"""
    """POST /api/v1/ledger/vendors - Create vendor (admin-only)"""
    if request.method == "GET":
        if not IsAuthenticatedReadOnly().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Permission denied",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = (
            Vendor.objects.filter(is_active=True)
            .select_related("vendor_type")
            .order_by("name")
        )
        serializer = VendorSerializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    else:  # POST
        if not IsAdmin().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Only ADMIN can create vendors",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        name = request.data.get("name")
        vendor_type_id = request.data.get("vendorTypeId")

        if not name:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "name is required",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If vendorTypeId not provided, create or get a default vendor type
        if not vendor_type_id:
            from apps.ledger.models import VendorType

            default_type, _ = VendorType.objects.get_or_create(
                name="Default", defaults={"is_active": True}
            )
            vendor_type_id = default_type.id

        try:
            vendor = services.create_vendor(request.user.id, name, vendor_type_id)
            serializer = VendorSerializer(vendor)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
        except DomainError:
            raise
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "Vendor name already exists for this type",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def update_vendor(request, vendorId):
    """PATCH /api/v1/ledger/vendors/{vendorId} - Update vendor (admin-only)"""
    is_active = request.data.get("isActive")
    if is_active is None:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "isActive is required",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        vendor = services.update_vendor(request.user.id, vendorId, is_active=is_active)
        serializer = VendorSerializer(vendor)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise


# -----------------------------
# Subcontractors
# -----------------------------


@api_view(["GET", "POST"])
def list_or_create_subcontractors(request):
    """GET /api/v1/ledger/subcontractors - List subcontractors (read-only)"""
    """POST /api/v1/ledger/subcontractors - Create subcontractor (admin-only)"""
    if request.method == "GET":
        if not IsAuthenticatedReadOnly().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Permission denied",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = (
            Subcontractor.objects.filter(is_active=True)
            .select_related("scope", "assigned_site")
            .order_by("name")
        )
        serializer = SubcontractorSerializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    else:  # POST
        if not IsAdmin().has_permission(request, None):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Only ADMIN can create subcontractors",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        name = request.data.get("name")
        scope_id = request.data.get("scopeId")
        assigned_site_id = request.data.get("assignedSiteId")

        if not name or not scope_id:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "name and scopeId are required",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            subcontractor = services.create_subcontractor(
                request.user.id, name, scope_id, assigned_site_id
            )
            serializer = SubcontractorSerializer(subcontractor)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
        except DomainError:
            raise
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "Subcontractor name already exists for this scope",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def update_subcontractor(request, subcontractorId):
    """PATCH /api/v1/ledger/subcontractors/{subcontractorId} - Update subcontractor (admin-only)"""
    is_active = request.data.get("isActive")
    if is_active is None:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "isActive is required",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        subcontractor = services.update_subcontractor(
            request.user.id, subcontractorId, is_active=is_active
        )
        serializer = SubcontractorSerializer(subcontractor)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    except DomainError:
        raise


# -----------------------------
# Vendor Types
# -----------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def list_vendor_types(request):
    """GET /api/v1/ledger/vendor-types - List vendor types (read-only)"""
    queryset = VendorType.objects.filter(is_active=True).order_by("name")
    serializer = VendorTypeSerializer(queryset, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


# -----------------------------
# Subcontractor Scopes
# -----------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticatedReadOnly])
def list_subcontractor_scopes(request):
    """GET /api/v1/ledger/scopes - List subcontractor scopes (read-only)"""
    queryset = SubcontractorScope.objects.filter(is_active=True).order_by("name")
    serializer = SubcontractorScopeSerializer(queryset, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)
