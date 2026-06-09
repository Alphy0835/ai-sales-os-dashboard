from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.services.llm_adapter import LlmAdapterError


class LlmFallbackTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="LLM Co", slug="llm-fallback")
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
        for module in ModulePermission.Module.values:
            level = ModulePermission.Level.EDIT if module == ModulePermission.Module.SETTINGS else ModulePermission.Level.NONE
            ModulePermission.objects.update_or_create(
                user=self.manager, module=module, defaults={"level": level}
            )
        self.client = APIClient()
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "mgr@test.local", "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    @patch("ai.services.custom_reports.llm_available", return_value=True)
    @patch("ai.services.custom_reports.chat_completion", side_effect=LlmAdapterError("LLM unavailable"))
    def test_custom_report_falls_back_to_rule_based_engine(self, *_mocks):
        response = self.client.post(
            "/api/v1/manager/settings/custom-reports/",
            {
                "title": "Discovery focus",
                "description": "Отчёт по выявлению потребности discovery и вопросам клиенту",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["structured_query"]["engine"], "rule_based_v1")
        self.assertIn("discovery", response.data["structured_query"]["focus_stages"])
