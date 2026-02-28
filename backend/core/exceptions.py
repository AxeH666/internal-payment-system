"""
Domain exceptions for the Internal Payment Workflow System.

All exceptions follow the standard error format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable description",
        "details": {}
    }
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, code, message, details=None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DomainError):
    """Validation error - request body or parameters fail validation."""

    def __init__(self, message, details=None):
        super().__init__("VALIDATION_ERROR", message, details)


class InvalidStateError(DomainError):
    """Entity is not in the required state for the operation."""

    def __init__(self, message, details=None):
        super().__init__("INVALID_STATE", message, details)


class NotFoundError(DomainError):
    """Requested resource does not exist."""

    def __init__(self, message, details=None):
        super().__init__("NOT_FOUND", message, details)


class PermissionDeniedError(DomainError):
    """Authenticated user lacks required role."""

    def __init__(self, message, details=None):
        super().__init__("FORBIDDEN", message, details)


class PreconditionFailedError(DomainError):
    """One or more preconditions are not satisfied."""

    def __init__(self, message, details=None):
        super().__init__("PRECONDITION_FAILED", message, details)


def domain_exception_handler(exc, context):
    """
    Custom exception handler for domain exceptions.

    Returns standard error format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable description",
            "details": {}
        }
    }
    """
    # Handle domain exceptions
    if isinstance(exc, DomainError):
        status_code_map = {
            "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
            "INVALID_STATE": status.HTTP_409_CONFLICT,
            "NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "FORBIDDEN": status.HTTP_403_FORBIDDEN,
            "PRECONDITION_FAILED": status.HTTP_412_PRECONDITION_FAILED,
        }

        status_code = status_code_map.get(exc.code, status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
            status=status_code,
        )

    # Use default REST framework exception handler for other exceptions
    response = exception_handler(exc, context)

    if response is not None:
        # Format standard REST framework errors
        if "detail" in response.data:
            error_data = {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(response.data["detail"]),
                    "details": {},
                }
            }
        else:
            error_data = {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred",
                    "details": response.data,
                }
            }

        response.data = error_data

    # Log unhandled exceptions
    if response is None:
        logger.exception("Unhandled exception", exc_info=exc)
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
