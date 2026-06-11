from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from integrations.models import IntegrationSource, MetricSnapshot
from integrations.services.aggregation import build_metrics_summary


class SheetsDashboardMetricsTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Sheets Dash Co", slug="sheets-dash")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@dash.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        ModulePermission.objects.update_or_create(
            user=self.manager,
            module=ModulePermission.Module.DASHBOARD,
            defaults={"level": ModulePermission.Level.VIEW},
        )

        self.employee = User.objects.create_user(
            email="emp@dash.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )

        self.sheets_crm = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="Google Sheets CRM",
            status=IntegrationSource.Status.CONNECTED,
            config_json={"provider": "google_sheets", "spreadsheet_id": "sheet-1"},
        )
        self.telephony = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.TELEPHONY,
            name="Tel",
            status=IntegrationSource.Status.CONNECTED,
        )

        today = timezone.localdate()
        MetricSnapshot.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.employee,
            source=self.telephony,
            metric_key="calls",
            period_date=today,
            value=Decimal("5"),
        )

        today = timezone.localdate()
        MetricSnapshot.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.employee,
            source=self.sheets_crm,
            metric_key="deals",
            period_date=today,
            value=Decimal("3"),
        )

        self.client = APIClient()

    def _login(self, email):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": email, "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_build_metrics_summary_deals_from_metric_snapshots(self):
        summary = build_metrics_summary(actor=self.manager, period="today")
        deals = summary["metrics"]["deals"]
        self.assertTrue(deals["available"])
        self.assertEqual(deals["value"], 3.0)
        self.assertTrue(summary["metrics"]["calls"]["available"])
        self.assertEqual(summary["metrics"]["calls"]["value"], 5.0)
        self.assertFalse(summary["metrics"]["revenue"]["available"])

    def test_manager_dashboard_sheets_only_deals_non_empty(self):
        self._login("mgr@dash.local")
        response = self.client.get("/api/v1/manager/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        deals = response.data["periods"]["today"]["metrics"]["deals"]
        self.assertTrue(deals["available"])
        self.assertEqual(deals["value"], 3.0)

    def test_demo_crm_still_uses_metric_snapshot(self):
        demo_tenant = Tenant.objects.create(name="Demo Co", slug="demo-co")
        demo_ws = Workspace.objects.create(tenant=demo_tenant, name="Demo WS")
        demo_mgr = User.objects.create_user(
            email="demo@mgr.local",
            password="pass1234",
            tenant=demo_tenant,
            workspace=demo_ws,
            full_name="Demo Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=demo_mgr, workspace=demo_ws)
        demo_emp = User.objects.create_user(
            email="demo@emp.local",
            password="pass1234",
            tenant=demo_tenant,
            workspace=demo_ws,
            full_name="Demo Employee",
            role=User.Role.EMPLOYEE,
        )
        demo_crm = IntegrationSource.objects.create(
            tenant=demo_tenant,
            workspace=demo_ws,
            source_type=IntegrationSource.SourceType.CRM,
            name="Demo CRM",
            status=IntegrationSource.Status.CONNECTED,
        )
        today = timezone.localdate()
        MetricSnapshot.objects.create(
            tenant=demo_tenant,
            workspace=demo_ws,
            user=demo_emp,
            source=demo_crm,
            metric_key="deals",
            period_date=today,
            value=Decimal("7"),
        )

        summary = build_metrics_summary(actor=demo_mgr, period="today")
        self.assertEqual(summary["metrics"]["deals"]["value"], 7.0)

    def test_manager_without_scoped_employees_gets_zero_deals_not_tenant_wide(self):
        lone_mgr = User.objects.create_user(
            email="lonemgr@dash.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Lone Manager",
            role=User.Role.MANAGER,
        )
        ModulePermission.objects.update_or_create(
            user=lone_mgr,
            module=ModulePermission.Module.DASHBOARD,
            defaults={"level": ModulePermission.Level.VIEW},
        )
        summary = build_metrics_summary(actor=lone_mgr, period="today")
        self.assertEqual(summary["metrics"]["deals"]["value"], 0.0)

    def test_tenant_wide_sheets_leads_with_null_workspace_counted(self):
        tenant_wide = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=None,
            source_type=IntegrationSource.SourceType.CRM,
            name="Tenant Sheets",
            status=IntegrationSource.Status.CONNECTED,
            config_json={"provider": "google_sheets", "spreadsheet_id": "sheet-2"},
        )
        MetricSnapshot.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.employee,
            source=tenant_wide,
            metric_key="deals",
            period_date=timezone.localdate(),
            value=Decimal("1"),
        )
        summary = build_metrics_summary(actor=self.manager, period="today")
        self.assertEqual(summary["metrics"]["deals"]["value"], 4.0)

    def test_sheets_deals_combined_with_demo_snapshot(self):
        demo_crm = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="Demo CRM",
            status=IntegrationSource.Status.CONNECTED,
        )
        MetricSnapshot.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.employee,
            source=demo_crm,
            metric_key="deals",
            period_date=timezone.localdate(),
            value=Decimal("2"),
        )
        summary = build_metrics_summary(actor=self.manager, period="today")
        self.assertEqual(summary["metrics"]["deals"]["value"], 5.0)
