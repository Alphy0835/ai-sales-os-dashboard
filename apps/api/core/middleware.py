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
