from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import AnalyticsReport, QualityCriterion
from integrations.models import ConversationRecording, IntegrationSource, Transcription
from integrations.tasks import transcribe_recording_task


class Stage005TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test-ai")
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
            analytics=ModulePermission.Level.VIEW,
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

    def test_manager_lists_and_creates_criteria(self):
        self._login("mgr@test.local")
        listing = self.client.get("/api/v1/manager/settings/quality-criteria/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 2)

        created = self.client.post(
            "/api/v1/manager/settings/quality-criteria/",
            {
                "name": "Closing",
                "funnel_stage": QualityCriterion.FunnelStage.CLOSING,
                "keywords": "договор, следующ",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QualityCriterion.objects.filter(tenant=self.tenant).count(), 3)

    def test_view_only_cannot_edit_criteria(self):
        self._login("viewmgr@test.local")
        response = self.client.post(
            "/api/v1/manager/settings/quality-criteria/",
            {"name": "X", "funnel_stage": "closing", "keywords": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_run_report_with_transcriptions(self):
        self._login("mgr@test.local")
        response = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.workspace.id),
                "employee_id": str(self.employee.id),
                "template": AnalyticsReport.Template.STANDARD_QUALITY,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], AnalyticsReport.Status.COMPLETED)
        self.assertIn("stages", response.data["canvas"])
        self.assertGreaterEqual(response.data["recordings_analyzed"], 1)

    def test_run_report_without_transcriptions_fails_clearly(self):
        Transcription.objects.all().delete()
        self._login("mgr@test.local")
        response = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.workspace.id),
                "employee_id": str(self.employee.id),
                "template": AnalyticsReport.Template.STANDARD_QUALITY,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("transcriptions", response.data["error_message"].lower())

    def test_view_only_cannot_run_report(self):
        self._login("viewmgr@test.local")
        response = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.workspace.id),
                "template": AnalyticsReport.Template.STANDARD_QUALITY,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_updated_criterion_reflected_in_report(self):
        self._login("mgr@test.local")
        criterion = QualityCriterion.objects.get(name="Greeting")
        self.client.patch(
            f"/api/v1/manager/settings/quality-criteria/{criterion.id}/",
            {"keywords": "missingword"},
            format="json",
        )
        response = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.workspace.id),
                "employee_id": str(self.employee.id),
                "template": AnalyticsReport.Template.STANDARD_QUALITY,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        scores = {c["name"]: c["score"] for c in response.data["canvas"]["criteria"]}
        self.assertEqual(scores["Greeting"], 0)
