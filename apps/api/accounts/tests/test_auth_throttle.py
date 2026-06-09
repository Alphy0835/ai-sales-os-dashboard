from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Tenant, User, Workspace
from accounts.views import LoginRateThrottle


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "accounts.authentication.CookieJWTAuthentication",
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
        "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_THROTTLE_RATES": {"login": "2/min", "agent": None},
    }
)
class LoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        LoginRateThrottle.rate = "2/min"
        tenant = Tenant.objects.create(name="Throttle Co", slug="throttle")
        workspace = Workspace.objects.create(tenant=tenant, name="ОП Москва")
        User.objects.create_user(
            email="user@test.local",
            password="pass1234",
            tenant=tenant,
            workspace=workspace,
            full_name="Test User",
            role=User.Role.EMPLOYEE,
        )
        self.client = APIClient()

    def tearDown(self):
        LoginRateThrottle.rate = None
        cache.clear()

    def test_login_returns_429_when_throttled(self):
        payload = {"email": "user@test.local", "password": "wrong-password"}
        for _ in range(2):
            response = self.client.post("/api/v1/auth/login/", payload, format="json")
            self.assertIn(
                response.status_code,
                (status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST),
            )

        throttled = self.client.post("/api/v1/auth/login/", payload, format="json")
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
