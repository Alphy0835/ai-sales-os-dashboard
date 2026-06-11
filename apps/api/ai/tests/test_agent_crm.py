from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import ManagerScope, Tenant, User, Workspace
from integrations.models import CrmLead, IntegrationSource
from ai.services.agent import generate_agent_reply


@override_settings(CRM_SYNC_INTERVAL_MINUTES=60)
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
            config_json={"provider": "google_sheets"},
            last_sync_at=timezone.now(),
        )
        CrmLead.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            integration_source=self.source,
            external_lead_id="L-10",
            client_name="Gamma Inc",
            pipeline_stage="Closing",
            status_stage="open",
            manager_email="emp@agent.local",
            employee=self.employee,
        )
        CrmLead.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            integration_source=self.source,
            external_lead_id="L-11",
            client_name="Delta Ltd",
            pipeline_stage="Qualification",
            status_stage="open",
            manager_email="emp@agent.local",
            employee=self.employee,
        )

    @patch("ai.services.agent.maybe_refresh_crm")
    def test_rule_based_crm_count_in_agent_reply(self, mock_refresh):
        reply, sources, warnings = generate_agent_reply(
            actor=self.manager,
            message="Сколько клиентов в CRM?",
        )
        self.assertIn("найдено клиентов: 2", reply.lower())
        self.assertIn("Данные на", reply)
        self.assertEqual(sources, [])
        self.assertEqual(warnings, [])
        mock_refresh.assert_called_once()

    @patch("ai.services.agent.maybe_refresh_crm")
    def test_rule_based_crm_list_in_agent_reply(self, mock_refresh):
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="Покажи список клиентов Gamma",
        )
        self.assertIn("Gamma Inc", reply)
        self.assertIn("Данные на", reply)

    @patch("ai.services.agent.maybe_refresh_crm")
    def test_employee_crm_query_scoped_to_self(self, mock_refresh):
        other = User.objects.create_user(
            email="other@agent.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Other",
            role=User.Role.EMPLOYEE,
        )
        CrmLead.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            integration_source=self.source,
            external_lead_id="L-99",
            client_name="Hidden Client",
            manager_email="other@agent.local",
            employee=other,
        )
        reply, _, _ = generate_agent_reply(
            actor=self.employee,
            message="Сколько клиентов?",
        )
        self.assertIn("найдено клиентов: 2", reply.lower())
        self.assertNotIn("Hidden Client", reply)

    @patch("ai.services.agent.chat_completion", return_value="Сфокусируйтесь на ценности продукта.")
    @patch("ai.services.agent.llm_available", return_value=True)
    @patch("ai.services.agent.maybe_refresh_crm")
    def test_coaching_question_skips_crm_and_uses_llm(self, mock_refresh, _mock_llm, _mock_chat):
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="У меня клиент говорит дорого, не знаю как ему ответить",
        )
        self.assertNotIn("CRM не найдены", reply)
        mock_refresh.assert_not_called()
        _mock_chat.assert_called_once()

    @patch("ai.services.agent.maybe_refresh_crm")
    def test_client_name_lookup_routes_to_crm(self, mock_refresh):
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="клиент Gamma",
        )
        self.assertIn("Gamma Inc", reply)
        self.assertIn("Данные на", reply)
        mock_refresh.assert_called_once()

    @patch("ai.services.agent.maybe_refresh_crm")
    def test_lookup_by_external_lead_id(self, mock_refresh):
        CrmLead.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            integration_source=self.source,
            external_lead_id="TW6090",
            client_name="Елена",
            pipeline_stage="Closing",
            status_stage="open",
            employee=None,
        )
        reply, _, _ = generate_agent_reply(
            actor=self.manager,
            message="Как зовут клиента TW6090",
        )
        self.assertIn("Елена", reply)
        self.assertNotIn("не найдены", reply.lower())
        mock_refresh.assert_called_once()
