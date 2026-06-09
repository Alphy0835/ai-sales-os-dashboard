from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import AnalyticsReport, CustomReport
from ai.services.agent import _recording_context
from integrations.models import ConversationRecording, IntegrationSource, Transcription


class ScopeIsolationTestCase(TestCase):
    """Regression tests: managers must not see data outside their workspace scope."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test-scope")
        self.moscow = Workspace.objects.create(tenant=self.tenant, name="ОП Москва")
        self.spb = Workspace.objects.create(tenant=self.tenant, name="ОП СПб")

        self.top_manager = User.objects.create_user(
            email="top@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.moscow,
            full_name="Top Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.top_manager, workspace=self.moscow)
        ManagerScope.objects.create(user=self.top_manager, workspace=self.spb)
        self._set_perms(self.top_manager, analytics=ModulePermission.Level.RUN, agent=ModulePermission.Level.USE)

        self.regional = User.objects.create_user(
            email="regional@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.moscow,
            full_name="Regional Manager",
            role=User.Role.MANAGER,
            manager=self.top_manager,
        )
        ManagerScope.objects.create(user=self.regional, workspace=self.moscow)
        self._set_perms(self.regional, analytics=ModulePermission.Level.VIEW, agent=ModulePermission.Level.USE)

        self.spb_employee = User.objects.create_user(
            email="emp-spb@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.spb,
            full_name="SPB Employee",
            role=User.Role.EMPLOYEE,
        )

        telephony = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.spb,
            source_type=IntegrationSource.SourceType.TELEPHONY,
            name="Tel SPB",
            status=IntegrationSource.Status.CONNECTED,
        )
        self.spb_recording = ConversationRecording.objects.create(
            tenant=self.tenant,
            workspace=self.spb,
            employee=self.spb_employee,
            integration_source=telephony,
            source_kind=ConversationRecording.SourceKind.TELEPHONY,
            client_name="SecretClient",
            status=ConversationRecording.Status.READY,
        )
        Transcription.objects.create(
            recording=self.spb_recording,
            status=Transcription.Status.COMPLETED,
            text="Конфиденциальный разговор по СПб",
        )

        AnalyticsReport.objects.create(
            tenant=self.tenant,
            author=self.top_manager,
            workspace=self.spb,
            template=AnalyticsReport.Template.STANDARD_QUALITY,
            status=AnalyticsReport.Status.COMPLETED,
            summary_text="SPB report",
        )

        self.spb_manager = User.objects.create_user(
            email="spb-mgr@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.spb,
            full_name="SPB Manager",
            role=User.Role.MANAGER,
            manager=self.top_manager,
        )
        ManagerScope.objects.create(user=self.spb_manager, workspace=self.spb)
        self._set_perms(
            self.spb_manager,
            analytics=ModulePermission.Level.VIEW,
            settings=ModulePermission.Level.EDIT,
        )

        CustomReport.objects.create(
            tenant=self.tenant,
            author=self.top_manager,
            title="Moscow custom report",
            description="Focus on greeting",
            structured_query={"focus_stages": ["greeting"]},
        )
        CustomReport.objects.create(
            tenant=self.tenant,
            author=self.spb_manager,
            title="SPB custom report",
            description="Focus on closing",
            structured_query={"focus_stages": ["closing"]},
        )

        self.client = APIClient()

    def _set_perms(self, user, **modules):
        defaults = {m: ModulePermission.Level.NONE for m in ModulePermission.Module.values}
        defaults.update(modules)
        for module, level in defaults.items():
            ModulePermission.objects.update_or_create(
                user=user, module=module, defaults={"level": level}
            )

    def _login(self, email):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": email, "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_reports_list_excludes_out_of_scope_workspace(self):
        self._login("regional@test.local")
        response = self.client.get("/api/v1/manager/analytics/reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_reports_list_includes_in_scope_workspace(self):
        self._login("top@test.local")
        response = self.client.get("/api/v1/manager/analytics/reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_custom_reports_list_excludes_out_of_scope_author_workspace(self):
        self._set_perms(self.regional, settings=ModulePermission.Level.VIEW)
        self._login("regional@test.local")
        response = self.client.get("/api/v1/manager/settings/custom-reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Moscow custom report")

    def test_custom_reports_list_includes_all_for_top_manager(self):
        self._set_perms(self.top_manager, settings=ModulePermission.Level.VIEW)
        self._login("top@test.local")
        response = self.client.get("/api/v1/manager/settings/custom-reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_agent_recording_context_respects_manager_scope(self):
        context_out_of_scope = _recording_context(self.regional, "SecretClient")
        self.assertEqual(context_out_of_scope, "")

        context_in_scope = _recording_context(self.top_manager, "SecretClient")
        self.assertIn("Конфиденциальный", context_in_scope)

    def test_agent_chat_unknown_session_returns_404(self):
        self._login("top@test.local")
        response = self.client.post(
            "/api/v1/manager/agent/chat/",
            {
                "message": "hello",
                "session_id": "00000000-0000-0000-0000-000000000000",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
