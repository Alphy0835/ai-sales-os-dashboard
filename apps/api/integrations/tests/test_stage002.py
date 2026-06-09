from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from integrations.models import ConversationRecording, IntegrationSource, MetricSnapshot, Transcription
from integrations.services.sync import run_source_sync


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class Stage002TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test-int")
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
        self._set_perms(self.manager, dashboard=ModulePermission.Level.VIEW)

        self.employee = User.objects.create_user(
            email="emp@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        self._set_perms(self.employee, dashboard=ModulePermission.Level.VIEW)

        self.crm = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
        )
        self.telephony = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.TELEPHONY,
            name="Telephony",
            status=IntegrationSource.Status.DEGRADED,
        )
        IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.REPORTING,
            name="Reporting",
            status=IntegrationSource.Status.DISCONNECTED,
        )
        run_source_sync(self.crm)
        run_source_sync(self.telephony)

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

    def test_metrics_partial_when_source_unavailable(self):
        self._login("mgr@test.local")
        response = self.client.get("/api/v1/integrations/metrics/?period=today")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completeness"], "partial")
        self.assertFalse(response.data["metrics"]["quality_score"]["available"])

    def test_metrics_today_for_employee(self):
        self._login("emp@test.local")
        response = self.client.get("/api/v1/integrations/metrics/?period=today")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["metrics"]["calls"]["value"], 0)

    def test_manual_recording_creates_transcription(self):
        self._login("emp@test.local")
        response = self.client.post(
            "/api/v1/integrations/recordings/",
            {
                "client_name": "Test Client",
                "employee_id": str(self.employee.id),
                "duration_seconds": 120,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recording = ConversationRecording.objects.get(id=response.data["id"])
        self.assertTrue(Transcription.objects.filter(recording=recording).exists())
        transcription = recording.transcription
        self.assertEqual(transcription.status, Transcription.Status.COMPLETED)

    def test_sources_list(self):
        self._login("mgr@test.local")
        response = self.client.get("/api/v1/integrations/sources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_transcription_endpoint(self):
        recording = ConversationRecording.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            source_kind=ConversationRecording.SourceKind.MANUAL,
            client_name="Client",
            status=ConversationRecording.Status.READY,
        )
        Transcription.objects.create(
            recording=recording,
            text="Hello",
            status=Transcription.Status.COMPLETED,
        )
        self._login("emp@test.local")
        response = self.client.get(f"/api/v1/integrations/recordings/{recording.id}/transcription/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Hello")
