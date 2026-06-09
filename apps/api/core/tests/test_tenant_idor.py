from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from analytics.models import ClientToReview
from integrations.models import ConversationRecording, Transcription


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
