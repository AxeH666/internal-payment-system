"""
Permission classes for role-based access control.

Role is read from request.user (authenticated via JWT).
Role is NEVER read from request body, query parameters, or headers.
"""

from rest_framework import permissions


class IsCreator(permissions.BasePermission):
    """Allow CREATOR role only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, "role"):
            return False

        if request.user.role == "CREATOR":
            return True

        return False


class IsApprover(permissions.BasePermission):
    """Allow APPROVER role only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, "role"):
            return False

        if request.user.role == "APPROVER":
            return True

        return False


class IsCreatorOrApprover(permissions.BasePermission):
    """Allow CREATOR or APPROVER roles."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, "role"):
            return False

        if request.user.role in ("CREATOR", "APPROVER"):
            return True

        return False


class IsAuthenticatedReadOnly(permissions.BasePermission):
    """Allow CREATOR, APPROVER, VIEWER for GET requests."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, "role"):
            return False

        # Allow all authenticated users with valid roles for GET
        if request.method == "GET":
            if request.user.role in ("CREATOR", "APPROVER", "VIEWER"):
                return True

        return False
