from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import AnalyticsReport, CustomReport, QualityCriterion
from integrations.models import ConversationRecording, IntegrationSource, Transcription
from integrations.tasks import transcribe_recording_task


class Stage007TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test-custom")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="ОП Москва")

        self.manager = User.objects.create_user(
            email="mgr@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        self._set_perms(
            self.manager,
            settings=ModulePermission.Level.EDIT,
            analytics=ModulePermission.Level.RUN,
        )

        self.view_manager = User.objects.create_user(
            email="viewmgr@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="View Manager",
            role=User.Role.MANAGER,
            manager=self.manager,
        )
        ManagerScope.objects.create(user=self.view_manager, workspace=self.workspace)
        self._set_perms(
            self.view_manager,
            settings=ModulePermission.Level.VIEW,
            analytics=ModulePermission.Level.RUN,
        )

        self.employee = User.objects.create_user(
            email="emp@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee One",
            role=User.Role.EMPLOYEE,
        )

        QualityCriterion.objects.create(
            tenant=self.tenant,
            name="Greeting",
            funnel_stage=QualityCriterion.FunnelStage.GREETING,
            keywords="представился, привет",
            sort_order=1,
        )
        QualityCriterion.objects.create(
            tenant=self.tenant,
            name="Discovery",
            funnel_stage=QualityCriterion.FunnelStage.DISCOVERY,
            keywords="потребность, уточнил",
            sort_order=2,
        )
        QualityCriterion.objects.create(
            tenant=self.tenant,
            name="Closing",
            funnel_stage=QualityCriterion.FunnelStage.CLOSING,
            keywords="договор, следующ",
            sort_order=3,
        )

        telephony = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.TELEPHONY,
            name="Tel",
            status=IntegrationSource.Status.CONNECTED,
        )
        recording = ConversationRecording.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            integration_source=telephony,
            source_kind=ConversationRecording.SourceKind.TELEPHONY,
            client_name="Client A",
            status=ConversationRecording.Status.UPLOADED,
        )
        Transcription.objects.create(recording=recording, status=Transcription.Status.PENDING)
        transcribe_recording_task(str(recording.id))

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

    def test_manager_creates_custom_report_with_structured_query(self):
        self._login("mgr@test.local")
        response = self.client.post(
            "/api/v1/manager/settings/custom-reports/",
            {
                "title": "Закрытие сделок",
                "description": "Фокус на этапе closing и следующих шагах с клиентом",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("closing", response.data["structured_query"]["focus_stages"])
        self.assertEqual(CustomReport.objects.filter(tenant=self.tenant).count(), 1)

    def test_view_only_cannot_create_custom_report(self):
        self._login("viewmgr@test.local")
        response = self.client.post(
            "/api/v1/manager/settings/custom-reports/",
            {"title": "X", "description": "test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_run_saved_custom_report_from_analytics(self):
        self._login("mgr@test.local")
        created = self.client.post(
            "/api/v1/manager/settings/custom-reports/",
            {
                "title": "Discovery focus",
                "description": "Отчёт по выявлению потребности и вопросам discovery",
            },
            format="json",
        )
        custom_id = created.data["id"]

        run = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.workspace.id),
                "employee_id": str(self.employee.id),
                "custom_report_id": custom_id,
            },
            format="json",
        )
        self.assertEqual(run.status_code, status.HTTP_201_CREATED)
        self.assertEqual(run.data["template"], AnalyticsReport.Template.CUSTOM)
        self.assertEqual(run.data["custom_report_title"], "Discovery focus")
        self.assertIn("Discovery focus", run.data["summary_text"])
        self.assertEqual(run.data["canvas"]["custom_report_id"], custom_id)
        stages = {item["stage"] for item in run.data["canvas"]["criteria"]}
        self.assertEqual(stages, {QualityCriterion.FunnelStage.DISCOVERY})

    def test_rerun_existing_custom_report(self):
        self._login("mgr@test.local")
        report = CustomReport.objects.create(
            tenant=self.tenant,
            author=self.manager,
            title="Closing rerun",
            description="closing и договор",
            structured_query={
                "focus_stages": [QualityCriterion.FunnelStage.CLOSING],
                "focus_keywords": ["closing"],
                "engine": "rule_based_v1",
            },
        )

        first = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.workspace.id),
                "custom_report_id": str(report.id),
            },
            format="json",
        )
        second = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.workspace.id),
                "custom_report_id": str(report.id),
            },
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnalyticsReport.objects.filter(custom_report=report).count(), 2)
