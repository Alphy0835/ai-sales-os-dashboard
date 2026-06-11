from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import ManagerScope, Tenant, User, Workspace
from analytics.models import ClientToReview
from integrations.models import IntegrationSource
from integrations.services.crm.query import CrmQueryFilters, query_crm_leads, resolve_vocabulary
from integrations.services.crm_adapter import encrypt_source_credentials


SERVICE_ACCOUNT = {
    "type": "service_account",
    "client_email": "sheets@test.iam.gserviceaccount.com",
    "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
}


@override_settings(AI_CREDENTIALS_KEY="test-credentials-key-32chars!!", CRM_SYNC_INTERVAL_MINUTES=60)
class CrmQueryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Query Co", slug="query-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@query.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        self.employee = User.objects.create_user(
            email="emp@query.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        self.other_employee = User.objects.create_user(
            email="other@query.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Other",
            role=User.Role.EMPLOYEE,
        )
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
            credentials_encrypted=encrypt_source_credentials(SERVICE_ACCOUNT),
            config_json={
                "provider": "google_sheets",
                "spreadsheet_id": "sheet-123",
                "crm_vocabulary": {
                    "stages": {"Closing": ["closing", "дожатие"]},
                    "statuses": {"open": ["open", "в работе"]},
                },
            },
            last_sync_at=timezone.now(),
        )
        self.sheet_rows = [
            {
                "lead_id": "L-1",
                "client_name": "Alpha Corp",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "emp@query.local",
                "supervisor_email": "",
                "pipeline_stage": "Closing",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
            {
                "lead_id": "L-2",
                "client_name": "Beta LLC",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "other@query.local",
                "supervisor_email": "",
                "pipeline_stage": "Qualification",
                "status_stage": "done",
                "recording_url": "",
                "needs_review": "",
            },
        ]
        ClientToReview.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            client_external_id="L-1",
            client_name="Alpha Corp",
            reason="Needs review",
        )

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    def test_count_all_scoped_leads_for_manager(self, mock_read):
        mock_read.return_value = self.sheet_rows
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(),
            mode="count",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 2)
        self.assertIsNotNone(result["as_of"])

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    def test_employee_sees_only_own_leads(self, mock_read):
        mock_read.return_value = self.sheet_rows
        result = query_crm_leads(
            self.employee,
            filters=CrmQueryFilters(),
            mode="count",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    def test_pipeline_stage_vocabulary_filter(self, mock_read):
        mock_read.return_value = self.sheet_rows
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(pipeline_stage="дожатие"),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["leads"][0]["client_name"], "Alpha Corp")

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    def test_search_filter(self, mock_read):
        mock_read.return_value = self.sheet_rows
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(search="Alpha"),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    def test_search_filter_matches_external_lead_id(self, mock_read):
        mock_read.return_value = self.sheet_rows
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(search="L-2"),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["leads"][0]["client_name"], "Beta LLC")

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    def test_manager_sees_unassigned_lead_in_scoped_workspace(self, mock_read):
        mock_read.return_value = self.sheet_rows + [
            {
                "lead_id": "TW6090",
                "client_name": "Елена",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "Не email",
                "supervisor_email": "",
                "pipeline_stage": "Closing",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
        ]
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(search="TW6090"),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["leads"][0]["client_name"], "Елена")

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    def test_needs_review_filter(self, mock_read):
        mock_read.return_value = self.sheet_rows
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(needs_review=True),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["leads"][0]["external_lead_id"], "L-1")

    def test_resolve_vocabulary_aliases(self):
        resolved = resolve_vocabulary(self.source, "stages", "closing")
        self.assertEqual(resolved, "Closing")
        status = resolve_vocabulary(self.source, "statuses", "в работе")
        self.assertEqual(status, "open")
