import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from integrations.models import IntegrationSource, MetricSnapshot
from integrations.services.crm_adapter import encrypt_source_credentials
from integrations.services.sync import run_source_sync


@override_settings(AI_CREDENTIALS_KEY="test-credentials-key-32chars!!")
class AmoCrmSyncTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="CRM Co", slug="crm-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@crm.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        ModulePermission.objects.update_or_create(
            user=self.manager,
            module=ModulePermission.Module.SETTINGS,
            defaults={"level": ModulePermission.Level.EDIT},
        )
        self.employee = User.objects.create_user(
            email="emp@crm.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        creds = encrypt_source_credentials(
            {"access_token": "test-token", "subdomain": "demo"}
        )
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="amoCRM",
            status=IntegrationSource.Status.CONNECTED,
            external_id="demo",
            credentials_encrypted=creds,
            config_json={"won_status_ids": [142]},
        )

    @patch("integrations.services.crm.amocrm._request_json")
    def test_amocrm_sync_creates_metric_snapshots(self, mock_request):
        mock_request.side_effect = [
            {"_embedded": {"users": [{"id": 42, "email": "emp@crm.local"}]}},
            {
                "_embedded": {
                    "leads": [
                        {"status_id": 142, "price": 100000, "closed_at": 1},
                        {"status_id": 142, "price": 50000, "closed_at": 1},
                    ]
                }
            },
        ]
        run_source_sync(self.source)
        self.source.refresh_from_db()
        self.assertEqual(self.source.status, IntegrationSource.Status.CONNECTED)
        deals = MetricSnapshot.objects.get(
            user=self.employee, source=self.source, metric_key="deals"
        )
        revenue = MetricSnapshot.objects.get(
            user=self.employee, source=self.source, metric_key="revenue"
        )
        self.assertEqual(deals.value, Decimal("2"))
        self.assertEqual(revenue.value, Decimal("150000"))

    @patch("integrations.services.crm.amocrm._request_json")
    def test_amocrm_api_error_sets_source_error(self, mock_request):
        from integrations.services.crm_adapter import CrmAdapterError

        mock_request.side_effect = CrmAdapterError("amoCRM HTTP 401: unauthorized")
        run_source_sync(self.source)
        self.source.refresh_from_db()
        self.assertEqual(self.source.status, IntegrationSource.Status.ERROR)
        self.assertIn("401", self.source.last_error)

    def test_demo_sync_without_credentials(self):
        demo_source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="Demo CRM",
            status=IntegrationSource.Status.CONNECTED,
        )
        run_source_sync(demo_source)
        self.assertTrue(
            MetricSnapshot.objects.filter(source=demo_source, metric_key="deals").exists()
        )
