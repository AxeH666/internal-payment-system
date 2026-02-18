import logging
import uuid
from contextvars import ContextVar

# Context var for request_id so logging filter can access it (Gunicorn logs
# don't have record.request; they run in the same request context).
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_current_request_id() -> str | None:
    """Return the current request_id from context, for logging."""
    return _request_id_ctx.get()


class RequestIDFilter(logging.Filter):
    """Injects request_id into log records for structured logging."""

    def filter(self, record):
        # Django logs may pass extra={"request": request}; Gunicorn logs use contextvar
        request = getattr(record, "request", None)
        record.request_id = (
            getattr(request, "request_id", None) or get_current_request_id()
        )
        return True


class RequestIDMiddleware:
    """
    Injects X-Request-ID into:
    - request object
    - response header
    - logging context (via request attribute)
    """

    HEADER_NAME = "HTTP_X_REQUEST_ID"
    RESPONSE_HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.HEADER_NAME)

        if not request_id:
            request_id = str(uuid.uuid4())

        request.request_id = request_id
        _request_id_ctx.set(request_id)

        response = self.get_response(request)
        response[self.RESPONSE_HEADER] = request_id
        return response


class IdempotencyKeyMiddleware:
    """Enforce idempotency key requirement on mutation endpoints."""

    MUTATION_METHODS = ["POST", "PATCH", "PUT"]
    EXCLUDED_PATHS = ["/api/v1/auth/login", "/api/health/"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in self.MUTATION_METHODS:
            if not any(
                request.path.startswith(excluded) for excluded in self.EXCLUDED_PATHS
            ):
                idempotency_key = request.headers.get("Idempotency-Key")
                if not idempotency_key:
                    from django.http import JsonResponse

                    return JsonResponse(
                        {
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Idempotency-Key header is required for mutation operations",
                                "details": {},
                            }
                        },
                        status=400,
                    )
                request.idempotency_key = idempotency_key

        return self.get_response(request)
