from django.test import TestCase

from ai.services.agent_orchestrator import (
    AgentPlan,
    emergency_plan_from_message,
    looks_like_json_plan,
    parse_agent_plan,
)
from ai.services.crm_tools import format_crm_result


class AgentPlanParseTests(TestCase):
    def test_looks_like_json(self):
        self.assertTrue(looks_like_json_plan('{"crm": {"search": "TW26055"}}'))
        self.assertFalse(looks_like_json_plan("Привет, менеджер"))

    def test_parse_crm_search(self):
        plan = parse_agent_plan('{"crm": {"search": "TW26055", "count": false}}')
        self.assertIsNotNone(plan)
        self.assertEqual(plan.crm_search, "TW26055")
        self.assertFalse(plan.crm_count)
        self.assertTrue(plan.needs_fetch())

    def test_parse_kb_only(self):
        plan = parse_agent_plan('{"kb": {"query": "возражение дорого"}}')
        self.assertEqual(plan.kb_query, "возражение дорого")
        self.assertIsNone(plan.crm_search)

    def test_emergency_lead_id(self):
        plan = emergency_plan_from_message("TW26055 как клиента зовут?")
        self.assertEqual(plan.crm_search, "TW26055")

    def test_emergency_count(self):
        plan = emergency_plan_from_message("Сколько клиентов в CRM?")
        self.assertTrue(plan.crm_count)

    def test_emergency_comment_from_dialog(self):
        class _Msg:
            def __init__(self, content):
                self.content = content

        dialog = [_Msg("Дмитрий — клиент с ID TW154676.")]
        plan = emergency_plan_from_message("А коментарий посмотреть?", dialog)
        self.assertEqual(plan.crm_search, "TW154676")

    def test_needs_fetch_false(self):
        plan = AgentPlan()
        self.assertFalse(plan.needs_fetch())


class FormatCrmResultTests(TestCase):
    def test_includes_comment(self):
        result = {
            "count": 1,
            "leads": [
                {
                    "external_lead_id": "TW154676",
                    "client_name": "Дмитрий",
                    "pipeline_stage": "2 ПСМ",
                    "status_stage": "НАЗНАЧЕН",
                    "communication_comment": "Строительство частного дома",
                }
            ],
        }
        text = format_crm_result(result, "list")
        self.assertIn("комментарий: Строительство частного дома", text)
