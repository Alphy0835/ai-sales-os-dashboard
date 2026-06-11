from unittest.mock import patch

from django.test import TestCase, override_settings

from accounts.models import Tenant, User, Workspace
from integrations.services.crm.query import CrmQueryFilters
from ai.services.crm_tools import (
    _parse_crm_intent_payload,
    detect_crm_intent,
)


class CrmIntentParseTests(TestCase):
    def test_parse_false_intent(self):
        needs, filters, mode = _parse_crm_intent_payload({"needs_crm_query": False})
        self.assertFalse(needs)
        self.assertIsNone(filters)
        self.assertEqual(mode, "list")

    def test_parse_count_intent(self):
        needs, filters, mode = _parse_crm_intent_payload(
            {"needs_crm_query": True, "mode": "count"}
        )
        self.assertTrue(needs)
        self.assertEqual(mode, "count")
        self.assertIsNotNone(filters)

    def test_parse_search_intent(self):
        needs, filters, mode = _parse_crm_intent_payload(
            {
                "needs_crm_query": True,
                "mode": "list",
                "search": "TW26055",
            }
        )
        self.assertTrue(needs)
        self.assertEqual(filters.search, "TW26055")


@override_settings(AI_CREDENTIALS_KEY="test-credentials-key-32chars!!")
class DetectCrmIntentTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Intent Co", slug="intent-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@intent.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            role=User.Role.MANAGER,
        )

    @patch("ai.services.crm_tools._llm_classify_crm_intent")
    def test_uses_llm_result_when_available(self, mock_classify):
        mock_classify.return_value = (True, CrmQueryFilters(search="TW26055"), "list")
        needs, filters, mode = detect_crm_intent("TW26055 как клиента зовут?", self.manager)
        self.assertTrue(needs)
        self.assertEqual(filters.search, "TW26055")
        self.assertEqual(mode, "list")
        mock_classify.assert_called_once()

    @patch("ai.services.crm_tools._llm_classify_crm_intent", return_value=None)
    def test_emergency_fallback_count_when_llm_unavailable(self, _mock_classify):
        needs, filters, mode = detect_crm_intent("Сколько клиентов в CRM?", self.manager)
        self.assertTrue(needs)
        self.assertEqual(mode, "count")

    @patch(
        "ai.services.crm_tools._llm_classify_crm_intent",
        return_value=(False, None, "list"),
    )
    def test_coaching_not_routed_to_crm(self, _mock_classify):
        needs, filters, mode = detect_crm_intent(
            "У меня клиент говорит дорого, не знаю как ему ответить",
            self.manager,
        )
        self.assertFalse(needs)
        self.assertIsNone(filters)
