from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import AnalyticsReport
from ai.throttles import AnalyticsReportRunThrottle, CustomReportThrottle


THROTTLE_SETTINGS = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "login": None,
        "agent": None,
        "analytics_run": "2/min",
        "custom_report": "2/min",
        "recording_upload": None,
    },
}


@override_settings(REST_FRAMEWORK=THROTTLE_SETTINGS)
class AnalyticsReportRunThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        AnalyticsReportRunThrottle.rate = "2/min"
        tenant = Tenant.objects.create(name="Throttle Co", slug="throttle-ai")
        workspace = Workspace.objects.create(tenant=tenant, name="ОП Москва")
        self.workspace = workspace
        self.manager = User.objects.create_user(
            email="mgr@test.local",
            password="pass1234",
            tenant=tenant,
            workspace=workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=workspace)
        for module in ModulePermission.Module.values:
            ModulePermission.objects.update_or_create(
                user=self.manager,
                module=module,
                defaults={
                    "level": (
                        ModulePermission.Level.RUN
                        if module == ModulePermission.Module.ANALYTICS
                        else ModulePermission.Level.NONE
                    )
                },
            )
        self.client = APIClient()
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "mgr@test.local", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def tearDown(self):
        AnalyticsReportRunThrottle.rate = None
        cache.clear()

    def test_analytics_report_run_returns_429_when_throttled(self):
        payload = {
            "workspace_id": str(self.workspace.id),
            "template": AnalyticsReport.Template.STANDARD_QUALITY,
        }
        for _ in range(2):
            response = self.client.post(
                "/api/v1/manager/analytics/reports/run/",
                payload,
                format="json",
            )
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        throttled = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            payload,
            format="json",
        )
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


@override_settings(REST_FRAMEWORK=THROTTLE_SETTINGS)
class CustomReportThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        CustomReportThrottle.rate = "2/min"
        tenant = Tenant.objects.create(name="Throttle Co", slug="throttle-cr")
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
        for module in ModulePermission.Module.values:
            ModulePermission.objects.update_or_create(
                user=self.manager,
                module=module,
                defaults={
                    "level": (
                        ModulePermission.Level.EDIT
                        if module == ModulePermission.Module.SETTINGS
                        else ModulePermission.Level.NONE
                    )
                },
            )
        self.client = APIClient()
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "mgr@test.local", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def tearDown(self):
        CustomReportThrottle.rate = None
        cache.clear()

    def test_custom_report_create_returns_429_when_throttled(self):
        payload = {"title": "Test report", "description": "Focus on discovery stage questions"}
        for i in range(2):
            response = self.client.post(
                "/api/v1/manager/settings/custom-reports/",
                {**payload, "title": f"Test report {i}"},
                format="json",
            )
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        throttled = self.client.post(
            "/api/v1/manager/settings/custom-reports/",
            {**payload, "title": "Test report 3"},
            format="json",
        )
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_custom_report_patch_returns_429_when_throttled(self):
        from ai.models import CustomReport

        report = CustomReport.objects.create(
            tenant=self.manager.tenant,
            title="Existing",
            description="Original focus on closing",
            structured_query={"engine": "rule_based_v1"},
            created_by=self.manager,
        )
        for i in range(2):
            response = self.client.patch(
                f"/api/v1/manager/settings/custom-reports/{report.id}/",
                {"description": f"Updated focus {i}"},
                format="json",
            )
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        throttled = self.client.patch(
            f"/api/v1/manager/settings/custom-reports/{report.id}/",
            {"description": "Updated focus 3"},
            format="json",
        )
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
