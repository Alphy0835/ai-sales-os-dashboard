import json

from django.test import TestCase

from accounts.models import Tenant, Workspace
from integrations.admin import HEADER_MAP_FIELDS, IntegrationSourceAdminForm, _header_map_field_name
from integrations.config_templates import GOOGLE_SHEETS_CONFIG_TEMPLATE
from integrations.models import IntegrationSource


class IntegrationSourceAdminFormTests(TestCase):
    def test_form_declares_header_map_fields_at_class_level(self):
        for internal_field in HEADER_MAP_FIELDS:
            self.assertIn(_header_map_field_name(internal_field), IntegrationSourceAdminForm.declared_fields)

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Admin Co", slug="admin-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="Sheets CRM",
            config_json={
                "provider": "google_sheets",
                "spreadsheet_id": "abc-123",
                "sheet_name": "Лиды",
                "header_map": {
                    "id лида": "lead_id",
                    "клиент": "client_name",
                    "телефон": "phone",
                    "город": "city",
                    "комментарий": "communication_comment",
                    "email менеджера": "manager_email",
                    "email супервайзера": "supervisor_email",
                    "этап воронки": "pipeline_stage",
                    "статус": "status_stage",
                    "ссылка на записи": "recording_url",
                    "разбор": "needs_review",
                },
                "skip_status_stages": ["done", "closed", "закрыт", "архив"],
                "review_rules": {
                    "empty_comment_on_active": False,
                    "auto_review_statuses": ["требует разбора"],
                },
                "crm_vocabulary": {
                    "stages": {"Closing": ["дожатие"]},
                    "statuses": {"open": ["в работе"]},
                },
            },
        )

    def test_form_loads_header_map_from_config_json(self):
        form = IntegrationSourceAdminForm(instance=self.source)
        self.assertEqual(form.fields["provider"].initial, "google_sheets")
        self.assertEqual(form.fields["spreadsheet_id"].initial, "abc-123")
        self.assertEqual(form.fields["sheet_name"].initial, "Лиды")
        self.assertEqual(form.fields["header_map_lead_id"].initial, "id лида")
        self.assertEqual(form.fields["header_map_client_name"].initial, "клиент")
        self.assertEqual(form.fields["header_map_needs_review"].initial, "разбор")

        advanced = json.loads(form.fields["advanced_config_json"].initial)
        self.assertEqual(advanced["review_rules"]["empty_comment_on_active"], False)
        self.assertIn("дожатие", advanced["crm_vocabulary"]["stages"]["Closing"])

    def test_form_save_merges_column_map_and_data_start_row(self):
        data = {
            "tenant": str(self.tenant.id),
            "workspace": str(self.workspace.id),
            "source_type": IntegrationSource.SourceType.CRM,
            "name": "Sheets CRM",
            "status": IntegrationSource.Status.DISCONNECTED,
            "is_enabled": True,
            "external_id": "",
            "credentials_json": "",
            "provider": "google_sheets",
            "spreadsheet_id": "sheet-1",
            "sheet_name": "ВОРОНКА",
            "data_start_row": "3",
            "column_map_lead_id": "A",
            "column_map_client_name": "B",
            "column_map_phone": "C",
            "advanced_config_json": "",
        }
        form = IntegrationSourceAdminForm(data=data, instance=self.source)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.config_json["column_map"]["lead_id"], "A")
        self.assertEqual(saved.config_json["column_map"]["client_name"], "B")
        self.assertEqual(saved.config_json["data_start_row"], 3)

    def test_form_save_merges_header_map_and_preserves_advanced_config(self):
        data = {
            "tenant": str(self.tenant.id),
            "workspace": str(self.workspace.id),
            "source_type": IntegrationSource.SourceType.CRM,
            "name": "Sheets CRM",
            "status": IntegrationSource.Status.DISCONNECTED,
            "is_enabled": True,
            "external_id": "",
            "credentials_json": "",
            "provider": "google_sheets",
            "spreadsheet_id": "new-sheet-id",
            "sheet_name": "Leads",
            "header_map_lead_id": "Lead ID",
            "header_map_client_name": "Company",
            "header_map_phone": "Phone",
            "header_map_city": "City",
            "header_map_communication_comment": "Comment",
            "header_map_manager_email": "Manager",
            "header_map_supervisor_email": "Supervisor",
            "header_map_pipeline_stage": "Stage",
            "header_map_status_stage": "Status",
            "header_map_recording_url": "Recording",
            "header_map_needs_review": "Review",
            "advanced_config_json": json.dumps(
                {
                    "review_rules": {"empty_comment_on_active": True, "auto_review_statuses": []},
                    "crm_vocabulary": GOOGLE_SHEETS_CONFIG_TEMPLATE["crm_vocabulary"],
                },
                ensure_ascii=False,
            ),
        }
        form = IntegrationSourceAdminForm(data=data, instance=self.source)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()

        self.assertEqual(saved.config_json["spreadsheet_id"], "new-sheet-id")
        self.assertEqual(saved.config_json["header_map"]["Lead ID"], "lead_id")
        self.assertEqual(saved.config_json["header_map"]["Company"], "client_name")
        self.assertEqual(saved.config_json["header_map"]["Review"], "needs_review")
        self.assertEqual(
            saved.config_json["skip_status_stages"],
            ["done", "closed", "закрыт", "архив"],
        )
        self.assertEqual(saved.config_json["review_rules"]["empty_comment_on_active"], True)
        self.assertEqual(
            saved.config_json["crm_vocabulary"],
            GOOGLE_SHEETS_CONFIG_TEMPLATE["crm_vocabulary"],
        )

    def test_form_uses_identity_header_map_when_fields_empty(self):
        data = {
            "tenant": str(self.tenant.id),
            "workspace": str(self.workspace.id),
            "source_type": IntegrationSource.SourceType.CRM,
            "name": "Sheets CRM",
            "status": IntegrationSource.Status.DISCONNECTED,
            "is_enabled": True,
            "external_id": "",
            "credentials_json": "",
            "provider": "google_sheets",
            "spreadsheet_id": "sheet-1",
            "sheet_name": "Leads",
            "advanced_config_json": "",
        }
        form = IntegrationSourceAdminForm(data=data, instance=self.source)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()

        for internal_field in GOOGLE_SHEETS_CONFIG_TEMPLATE["header_map"]:
            self.assertEqual(saved.config_json["header_map"][internal_field], internal_field)

    def test_form_save_preserves_amocrm_keys(self):
        amo_source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="amo CRM",
            config_json={
                "provider": "amocrm",
                "won_status_ids": [142, 143],
                "review_rules": {"empty_comment_on_active": False},
            },
        )
        data = {
            "tenant": str(self.tenant.id),
            "workspace": str(self.workspace.id),
            "source_type": IntegrationSource.SourceType.CRM,
            "name": "amo CRM",
            "status": IntegrationSource.Status.DISCONNECTED,
            "is_enabled": True,
            "external_id": "",
            "credentials_json": "",
            "provider": "amocrm",
            "spreadsheet_id": "",
            "sheet_name": "Leads",
            "advanced_config_json": json.dumps(
                {"review_rules": {"empty_comment_on_active": True}},
                ensure_ascii=False,
            ),
        }
        form = IntegrationSourceAdminForm(data=data, instance=amo_source)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()

        self.assertEqual(saved.config_json["provider"], "amocrm")
        self.assertEqual(saved.config_json["won_status_ids"], [142, 143])
        self.assertEqual(saved.config_json["review_rules"]["empty_comment_on_active"], True)
