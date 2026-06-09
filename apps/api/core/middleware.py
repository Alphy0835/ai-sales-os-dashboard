from django.middleware.security import SecurityMiddleware

_HEALTH_PATH_PREFIXES = ("/api/v1/health",)


class SecureProxySecurityMiddleware(SecurityMiddleware):
    """SecurityMiddleware that skips SSL redirect for internal health probes."""

    def process_request(self, request):
        if any(request.path.startswith(prefix) for prefix in _HEALTH_PATH_PREFIXES):
            return None
        return super().process_request(request)


class TenantMiddleware:
    """Attach tenant from authenticated user for downstream views."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        user = getattr(request, "user", None)
        if user and user.is_authenticated and hasattr(user, "tenant"):
            request.tenant = user.tenant
        return self.get_response(request)
