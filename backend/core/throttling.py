from rest_framework.throttling import UserRateThrottle


class MutationUserThrottle(UserRateThrottle):
    scope = "mutation_user"

    def allow_request(self, request, view):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return super().allow_request(request, view)
        return True


class IdempotencyThrottle(UserRateThrottle):
    scope = "idempotency"

    def allow_request(self, request, view):
        if request.method == "POST" and "HTTP_IDEMPOTENCY_KEY" in request.META:
            return super().allow_request(request, view)
        return True
