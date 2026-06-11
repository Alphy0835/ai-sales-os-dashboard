from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import ManagerScope, Tenant, User, Workspace
from integrations.models import IntegrationSource
from integrations.services.crm_adapter import encrypt_source_credentials
from ai.services.agent import generate_agent_reply
from ai.services.agent_prompts import CONTEXT_EMPTY


SERVICE_ACCOUNT = {
    "type": "service_account",
    "client_email": "sheets@test.iam.gserviceaccount.com",
    "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
}


def _mock_llm(actor, messages):
    last = messages[-1]["content"]
    if CONTEXT_EMPTY in last:
        lower = last.lower()
        if "сколько" in lower:
            return '{"crm": {"count": true}}'
        if "tw26055" in lower:
            return '{"crm": {"search": "TW26055"}}'
        if "tw6090" in lower:
            return '{"crm": {"search": "TW6090"}}'
        if "gamma" in lower:
            return '{"crm": {"search": "Gamma"}}'
        if "дорого" in lower:
            return "Сфокусируйтесь на ценности продукта."
    if "--- CRM ---" in last:
        if "найдено клиентов: 2" in last.lower():
            return "В CRM найдено клиентов: 2.\n\nДанные на 01.01.2025 12:00."
        if "gamma inc" in last.lower():
            return "Клиент Gamma Inc (этап: Closing, статус: open).\n\nДанные на 01.01.2025 12:00."
        if "елена" in last.lower():
            lead = "TW26055" if "tw26055" in last.lower() else "TW6090"
            return f"Клиент {lead} — Елена.\n\nДанные на 01.01.2025 12:00."
    return "OK"


@override_settings(AI_CREDENTIALS_KEY="test-credentials-key-32chars!!", CRM_SYNC_INTERVAL_MINUTES=60)
class AgentCrmTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Agent CRM Co", slug="agent-crm")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@agent.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        self.employee = User.objects.create_user(
            email="emp@agent.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
            credentials_encrypted=encrypt_source_credentials(SERVICE_ACCOUNT),
            config_json={"provider": "google_sheets", "spreadsheet_id": "sheet-123"},
            last_sync_at=timezone.now(),
        )
        self.sheet_rows = [
            {
                "lead_id": "L-10",
                "client_name": "Gamma Inc",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "emp@agent.local",
                "supervisor_email": "",
                "pipeline_stage": "Closing",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
            {
                "lead_id": "L-11",
                "client_name": "Delta Ltd",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "emp@agent.local",
                "supervisor_email": "",
                "pipeline_stage": "Qualification",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
        ]
        self.llm_patcher = patch(
            "ai.services.agent_orchestrator._call_llm",
            side_effect=_mock_llm,
        )
        self.llm_available_patcher = patch(
            "ai.services.agent_orchestrator.llm_available",
            return_value=True,
        )
        self.llm_patcher.start()
        self.llm_available_patcher.start()

    def tearDown(self):
        self.llm_patcher.stop()
        self.llm_available_patcher.stop()

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_llm_routed_crm_count_in_agent_reply(self, mock_refresh, mock_read):
        mock_read.return_value = self.sheet_rows
        reply, sources, warnings = generate_agent_reply(
            actor=self.manager,
            message="Сколько клиентов в CRM?",
        )
        self.assertIn("найдено клиентов: 2", reply.lower())
        self.assertIn("Данные на", reply)
        self.assertEqual(sources, [])
        self.assertEqual(warnings, [])
        mock_refresh.assert_called_once()

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_llm_routed_crm_list_in_agent_reply(self, mock_refresh, mock_read):
        mock_read.return_value = self.sheet_rows
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="Покажи список клиентов Gamma",
        )
        self.assertIn("Gamma Inc", reply)
        self.assertIn("Данные на", reply)

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_employee_crm_query_scoped_to_self(self, mock_refresh, mock_read):
        other = User.objects.create_user(
            email="other@agent.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Other",
            role=User.Role.EMPLOYEE,
        )
        mock_read.return_value = self.sheet_rows + [
            {
                "lead_id": "L-99",
                "client_name": "Hidden Client",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "other@agent.local",
                "supervisor_email": "",
                "pipeline_stage": "Qualification",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
        ]
        reply, _, _ = generate_agent_reply(
            actor=self.employee,
            message="Сколько клиентов?",
        )
        self.assertIn("найдено клиентов: 2", reply.lower())
        self.assertNotIn("Hidden Client", reply)

    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_coaching_question_skips_crm_and_uses_llm(self, mock_refresh):
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="У меня клиент говорит дорого, не знаю как ему ответить",
        )
        self.assertNotIn("CRM не найдены", reply)
        mock_refresh.assert_not_called()
        self.assertIn("ценности", reply.lower())

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_client_name_lookup_routes_to_crm(self, mock_refresh, mock_read):
        mock_read.return_value = self.sheet_rows
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="клиент Gamma",
        )
        self.assertIn("Gamma Inc", reply)
        self.assertIn("Данные на", reply)
        mock_refresh.assert_called_once()

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_lookup_by_lead_id_with_kak_zovut_phrasing(self, mock_refresh, mock_read):
        mock_read.return_value = self.sheet_rows + [
            {
                "lead_id": "TW26055",
                "client_name": "Елена",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "emp@agent.local",
                "supervisor_email": "",
                "pipeline_stage": "Closing",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
        ]
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="TW26055 как клиента зовут?",
        )
        self.assertIn("Елена", reply)
        self.assertNotIn("не найдены", reply.lower())

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_lookup_by_external_lead_id(self, mock_refresh, mock_read):
        mock_read.return_value = self.sheet_rows + [
            {
                "lead_id": "TW6090",
                "client_name": "Елена",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "emp@agent.local",
                "supervisor_email": "",
                "pipeline_stage": "Closing",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
        ]
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="Как зовут клиента TW6090",
        )
        self.assertIn("Елена", reply)
        self.assertNotIn("не найдены", reply.lower())
        mock_refresh.assert_called_once()

    @patch("integrations.services.crm.google_sheets_live.read_sheet_rows_cached")
    @patch("ai.services.agent_orchestrator.llm_available", return_value=False)
    @patch("ai.services.agent_orchestrator.maybe_refresh_crm")
    def test_llm_down_emergency_crm_fallback(self, mock_refresh, _mock_llm, mock_read):
        mock_read.return_value = self.sheet_rows + [
            {
                "lead_id": "TW26055",
                "client_name": "Елена",
                "phone": "",
                "city": "",
                "communication_comment": "",
                "manager_email": "emp@agent.local",
                "supervisor_email": "",
                "pipeline_stage": "Closing",
                "status_stage": "open",
                "recording_url": "",
                "needs_review": "",
            },
        ]
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="TW26055 как клиента зовут?",
        )
        self.assertIn("Елена", reply)
