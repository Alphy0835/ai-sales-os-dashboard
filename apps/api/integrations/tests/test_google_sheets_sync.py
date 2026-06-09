from unittest.mock import patch

from django.test import TestCase, override_settings

from accounts.models import Tenant, User, Workspace
from analytics.models import ClientToReview
from integrations.models import CrmLead, IntegrationSource
from integrations.services.crm_adapter import encrypt_source_credentials
from integrations.services.crm.google_sheets import sync_google_sheets
from integrations.services.sync import run_source_sync


SERVICE_ACCOUNT = {
    "type": "service_account",
    "client_email": "sheets@test.iam.gserviceaccount.com",
    "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
}


@override_settings(AI_CREDENTIALS_KEY="test-credentials-key-32chars!!")
class GoogleSheetsSyncTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Sheets Co", slug="sheets-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.employee = User.objects.create_user(
            email="emp@sheet.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Sheet Employee",
            role=User.Role.EMPLOYEE,
        )
        creds = encrypt_source_credentials(SERVICE_ACCOUNT)
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="Google Sheets CRM",
            status=IntegrationSource.Status.DISCONNECTED,
            credentials_encrypted=creds,
            config_json={
                "provider": "google_sheets",
                "spreadsheet_id": "sheet-123",
                "sheet_name": "Leads",
            },
        )

    def _parsed_rows(self):
        return [
            {
                "lead_id": "L-100",
                "client_name": "Acme Corp",
                "phone": "+79990001122",
                "city": "Moscow",
                "communication_comment": "Needs follow-up call",
                "manager_email": "emp@sheet.local",
                "supervisor_email": "mgr@sheet.local",
                "pipeline_stage": "Qualification",
                "status_stage": "open",
                "recording_url": "https://example.com/rec1",
            },
            {
                "lead_id": "L-200",
                "client_name": "Closed Deal",
                "phone": "phone",
                "city": "SPB",
                "communication_comment": "",
                "manager_email": "emp@sheet.local",
                "supervisor_email": "",
                "pipeline_stage": "Won",
                "status_stage": "done",
                "recording_url": "",
            },
        ]

    @patch("integrations.services.crm.google_sheets._read_sheet_rows")
    def test_google_sheets_sync_upserts_crm_leads_and_clients(self, mock_read):
        mock_read.return_value = self._parsed_rows()
        run_source_sync(self.source)
        self.source.refresh_from_db()

        self.assertEqual(self.source.status, IntegrationSource.Status.CONNECTED)
        lead = CrmLead.objects.get(external_lead_id="L-100", integration_source=self.source)
        self.assertEqual(lead.client_name, "Acme Corp")
        self.assertEqual(lead.employee_id, self.employee.id)
        self.assertEqual(lead.phone, "+79990001122")
        self.assertEqual(lead.city, "Moscow")

        closed = CrmLead.objects.get(external_lead_id="L-200", integration_source=self.source)
        self.assertEqual(closed.status_stage, "done")

        review = ClientToReview.objects.get(
            tenant=self.tenant,
            employee=self.employee,
            client_external_id="L-100",
        )
        self.assertEqual(review.client_name, "Acme Corp")
        self.assertEqual(review.reason, "Needs follow-up call")
        self.assertFalse(
            ClientToReview.objects.filter(client_external_id="L-200").exists()
        )

    @patch("integrations.services.crm.google_sheets._read_sheet_rows")
    def test_google_sheets_sync_updates_existing_lead(self, mock_read):
        CrmLead.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            integration_source=self.source,
            external_lead_id="L-100",
            client_name="Old Name",
        )
        mock_read.return_value = self._parsed_rows()
        run_source_sync(self.source)

        lead = CrmLead.objects.get(external_lead_id="L-100", integration_source=self.source)
        self.assertEqual(lead.client_name, "Acme Corp")
        self.assertEqual(CrmLead.objects.filter(integration_source=self.source).count(), 2)

    def test_google_sheets_missing_spreadsheet_sets_error(self):
        self.source.config_json = {"provider": "google_sheets"}
        self.source.save(update_fields=["config_json"])
        sync_google_sheets(self.source)
        self.source.refresh_from_db()
        self.assertEqual(self.source.status, IntegrationSource.Status.ERROR)
        self.assertIn("spreadsheet_id", self.source.last_error)
