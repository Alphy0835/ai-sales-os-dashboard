from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from analytics.models import ClientToReview
from integrations.models import IntegrationSource
from integrations.services.sync import run_source_sync


class Stage003TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test-dash")
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
            full_name="Employee One",
            role=User.Role.EMPLOYEE,
        )
        self._set_perms(self.employee, dashboard=ModulePermission.Level.VIEW)

        crm = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
        )
        telephony = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.TELEPHONY,
            name="Tel",
            status=IntegrationSource.Status.DEGRADED,
        )
        run_source_sync(crm)
        run_source_sync(telephony)

        ClientToReview.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            client_name="Client A",
            reason="Low quality",
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

    def test_manager_dashboard(self):
        self._login("mgr@test.local")
        response = self.client.get("/api/v1/manager/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("periods", response.data)
        self.assertIn("employees", response.data)
        self.assertIn("today", response.data["periods"])

    def test_manager_dashboard_drilldown(self):
        self._login("mgr@test.local")
        response = self.client.get(f"/api/v1/manager/dashboard/?user_id={self.employee.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["employees"]), 1)

    def test_manager_clients(self):
        self._login("mgr@test.local")
        response = self.client.get("/api/v1/manager/clients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_employee_dashboard(self):
        self._login("emp@test.local")
        response = self.client.get("/api/v1/employee/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("periods", response.data)
        self.assertIn("employees", response.data)
        self.assertIn("trend", response.data)
        self.assertIn("hero", response.data)
        self.assertEqual(len(response.data["employees"]), 1)
        self.assertEqual(response.data["employees"][0]["full_name"], "Employee One")

    def test_employee_cannot_access_manager_clients(self):
        self._login("emp@test.local")
        response = self.client.get("/api/v1/manager/clients/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_clients_with_clients_permission_only(self):
        self._set_perms(self.manager, dashboard=ModulePermission.Level.NONE, clients=ModulePermission.Level.VIEW)
        self._login("mgr@test.local")
        response = self.client.get("/api/v1/manager/clients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_manager_clients_denied_without_clients_or_dashboard(self):
        self._set_perms(self.manager, dashboard=ModulePermission.Level.NONE, clients=ModulePermission.Level.NONE)
        self._login("mgr@test.local")
        response = self.client.get("/api/v1/manager/clients/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
