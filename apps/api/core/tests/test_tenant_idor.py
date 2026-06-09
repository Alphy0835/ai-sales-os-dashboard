from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from analytics.models import ClientToReview
from ai.services.agent import generate_agent_reply
from integrations.models import ConversationRecording, CrmLead, IntegrationSource, Transcription


class CrossTenantIdorTests(TestCase):
    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="Tenant A", slug="tenant-a")
        self.tenant_b = Tenant.objects.create(name="Tenant B", slug="tenant-b")
        self.ws_a = Workspace.objects.create(tenant=self.tenant_a, name="A Москва")
        self.ws_b = Workspace.objects.create(tenant=self.tenant_b, name="B Москва")

        self.manager_a = self._create_manager("mgr-a@test.local", self.tenant_a, self.ws_a)
        self.employee_a = User.objects.create_user(
            email="emp-a@test.local",
            password="pass1234",
            tenant=self.tenant_a,
            workspace=self.ws_a,
            full_name="Employee A",
            role=User.Role.EMPLOYEE,
        )
        self.employee_b = User.objects.create_user(
            email="emp-b@test.local",
            password="pass1234",
            tenant=self.tenant_b,
            workspace=self.ws_b,
            full_name="Employee B",
            role=User.Role.EMPLOYEE,
        )

        self.foreign_recording = ConversationRecording.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            employee=self.employee_b,
            source_kind=ConversationRecording.SourceKind.MANUAL,
            client_name="Foreign Client",
            status=ConversationRecording.Status.READY,
        )
        Transcription.objects.create(
            recording=self.foreign_recording,
            text="Secret transcript",
            status=Transcription.Status.COMPLETED,
        )
        self.foreign_client = ClientToReview.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            employee=self.employee_b,
            client_name="Foreign Corp",
            reason="Needs review",
            priority=ClientToReview.Priority.HIGH,
            status=ClientToReview.Status.NEW,
        )
        self.foreign_source = IntegrationSource.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            source_type=IntegrationSource.SourceType.CRM,
            name="Foreign CRM",
            status=IntegrationSource.Status.CONNECTED,
            config_json={"provider": "google_sheets"},
            last_sync_at=timezone.now(),
        )
        CrmLead.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            integration_source=self.foreign_source,
            external_lead_id="FB-1",
            client_name="Foreign Secret Corp",
            pipeline_stage="Closing",
            status_stage="open",
            manager_email="emp-b@test.local",
            employee=self.employee_b,
        )
        self.local_source = IntegrationSource.objects.create(
            tenant=self.tenant_a,
            workspace=self.ws_a,
            source_type=IntegrationSource.SourceType.CRM,
            name="Local CRM",
            status=IntegrationSource.Status.CONNECTED,
            config_json={"provider": "google_sheets"},
            last_sync_at=timezone.now(),
        )
        CrmLead.objects.create(
            tenant=self.tenant_a,
            workspace=self.ws_a,
            integration_source=self.local_source,
            external_lead_id="LA-1",
            client_name="Local Client",
            pipeline_stage="Qualification",
            status_stage="open",
            manager_email="emp-a@test.local",
            employee=self.employee_a,
        )

        self.client = APIClient()
        self._login(self.manager_a)

    def _create_manager(self, email, tenant, workspace):
        manager = User.objects.create_user(
            email=email,
            password="pass1234",
            tenant=tenant,
            workspace=workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=manager, workspace=workspace)
        for module in ModulePermission.Module.values:
            level = ModulePermission.Level.NONE
            if module in (
                ModulePermission.Module.DASHBOARD,
                ModulePermission.Module.REVIEWS,
            ):
                level = ModulePermission.Level.EDIT
            ModulePermission.objects.update_or_create(
                user=manager, module=module, defaults={"level": level}
            )
        return manager

    def _login(self, user):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_foreign_recording_detail_returns_404(self):
        response = self.client.get(f"/api/v1/integrations/recordings/{self.foreign_recording.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_foreign_recording_transcription_returns_404(self):
        response = self.client.get(
            f"/api/v1/integrations/recordings/{self.foreign_recording.id}/transcription/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_foreign_client_id_rejected_on_review_create(self):
        response = self.client.post(
            "/api/v1/manager/reviews/",
            {
                "employee_id": str(self.employee_a.id),
                "workspace_id": str(self.ws_a.id),
                "client_id": str(self.foreign_client.id),
                "comment": "Cross-tenant attempt",
                "tasks": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("client_id", response.data)

    @override_settings(CRM_SYNC_INTERVAL_MINUTES=60)
    @patch("ai.services.agent.maybe_refresh_crm")
    def test_cross_tenant_crm_lead_not_exposed_via_agent(self, mock_refresh):
        reply, _, _ = generate_agent_reply(
            actor=self.manager_a,
            message="Покажи список клиентов Foreign Secret Corp",
        )
        self.assertNotIn("Foreign Secret Corp", reply)
        mock_refresh.assert_called_once()

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("integrations.views.sync_integration_source.delay")
    def test_foreign_integration_source_sync_returns_404(self, mock_delay):
        ModulePermission.objects.update_or_create(
            user=self.manager_a,
            module=ModulePermission.Module.SETTINGS,
            defaults={"level": ModulePermission.Level.EDIT},
        )
        response = self.client.post(
            f"/api/v1/integrations/sources/{self.foreign_source.id}/sync/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_delay.assert_not_called()
