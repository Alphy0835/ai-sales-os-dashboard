from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.throttles import AgentRateThrottle


THROTTLE_SETTINGS = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "login": None,
        "agent": "2/min",
        "analytics_run": None,
        "custom_report": None,
        "recording_upload": None,
    },
}


@override_settings(REST_FRAMEWORK=THROTTLE_SETTINGS)
class AgentThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        AgentRateThrottle.rate = "2/min"
        tenant = Tenant.objects.create(name="Throttle Co", slug="throttle-agent")
        workspace = Workspace.objects.create(tenant=tenant, name="ОП Москва")
        self.manager = User.objects.create_user(
            email="mgr@test.local",
            password="pass1234",
            tenant=tenant,
            workspace=workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=workspace)
        ModulePermission.objects.update_or_create(
            user=self.manager,
            module=ModulePermission.Module.AGENT,
            defaults={"level": ModulePermission.Level.USE},
        )
        self.client = APIClient()
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "mgr@test.local", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def tearDown(self):
        AgentRateThrottle.rate = None
        cache.clear()

    def test_agent_chat_returns_429_when_throttled(self):
        payload = {"message": "Как работать с возражениями?"}
        for _ in range(2):
            response = self.client.post(
                "/api/v1/manager/agent/chat/",
                payload,
                format="json",
            )
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        throttled = self.client.post(
            "/api/v1/manager/agent/chat/",
            payload,
            format="json",
        )
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
