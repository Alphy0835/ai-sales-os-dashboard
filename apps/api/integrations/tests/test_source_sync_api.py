from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from integrations.models import IntegrationSource


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class IntegrationSourceSyncApiTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Sync Co", slug="sync-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@sync.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        for module, level in (
            (ModulePermission.Module.DASHBOARD, ModulePermission.Level.VIEW),
            (ModulePermission.Module.SETTINGS, ModulePermission.Level.EDIT),
        ):
            ModulePermission.objects.update_or_create(
                user=self.manager, module=module, defaults={"level": level}
            )
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
        )
        self.client = APIClient()

    def _login(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "mgr@sync.local", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    @patch("integrations.views.sync_integration_source.delay")
    def test_manual_sync_queues_task(self, mock_delay):
        self._login()
        response = self.client.post(f"/api/v1/integrations/sources/{self.source.id}/sync/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_delay.assert_called_once_with(str(self.source.id))
