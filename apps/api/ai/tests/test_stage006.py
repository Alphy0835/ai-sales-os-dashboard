from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import KnowledgeArticle


class Stage006TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test-kb")
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
        self._set_perms(self.manager, settings=ModulePermission.Level.EDIT, agent=ModulePermission.Level.USE)

        self.employee = User.objects.create_user(
            email="emp@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee One",
            role=User.Role.EMPLOYEE,
        )
        self._set_perms(self.employee, agent=ModulePermission.Level.USE)

        self.no_agent = User.objects.create_user(
            email="noagent@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="No Agent",
            role=User.Role.EMPLOYEE,
        )
        self._set_perms(self.no_agent, agent=ModulePermission.Level.NONE)

        KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Product guide",
            category=KnowledgeArticle.Category.PRODUCT,
            tags="продукт, crm",
            content="Описание продукта CRM для продаж.",
            access_level=KnowledgeArticle.AccessLevel.ALL,
        )
        KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Manager strategy",
            category=KnowledgeArticle.Category.CASE,
            tags="стратегия",
            content="Секретная стратегия только для руководителей.",
            access_level=KnowledgeArticle.AccessLevel.MANAGER,
        )

        self.client = APIClient()

    def _set_perms(self, user, **modules):
        defaults = {m: ModulePermission.Level.NONE for m in ModulePermission.Module.values}
        defaults.update(modules)
        for module, level in defaults.items():
            ModulePermission.objects.update_or_create(
                user=user, module=module, defaults={"level": level}
            )

    def _login(self, email):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": email, "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_manager_creates_knowledge_article(self):
        self._login("mgr@test.local")
        response = self.client.post(
            "/api/v1/manager/settings/knowledge/",
            {
                "title": "New playbook",
                "category": "objection",
                "content": "How to handle timing objection",
                "tags": "время, возражение",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(KnowledgeArticle.objects.filter(tenant=self.tenant).count(), 3)

    def test_manager_agent_uses_knowledge(self):
        self._login("mgr@test.local")
        response = self.client.post(
            "/api/v1/manager/agent/chat/",
            {"message": "расскажи про продукт crm", "client_name": "Client A", "client_note": "Нужен разбор"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assistant = [m for m in response.data["messages"] if m["role"] == "assistant"][-1]
        self.assertIn("Product guide", assistant["content"])
        self.assertTrue(assistant["sources"])

    def test_employee_agent_blocks_manager_only_material(self):
        self._login("emp@test.local")
        response = self.client.post(
            "/api/v1/manager/agent/chat/" if False else "/api/v1/employee/agent/chat/",
            {"message": "стратегия для руководителя"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assistant = [m for m in response.data["messages"] if m["role"] == "assistant"][-1]
        self.assertIn("недоступ", assistant["content"].lower())

    def test_employee_without_agent_permission_forbidden(self):
        self._login("noagent@test.local")
        response = self.client.post(
            "/api/v1/employee/agent/chat/",
            {"message": "help"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_new_article_reflected_in_agent_answer(self):
        self._login("mgr@test.local")
        self.client.post(
            "/api/v1/manager/settings/knowledge/",
            {
                "title": "UniqueTokenArticle",
                "category": "other",
                "content": "UniqueTokenContent for agent retrieval",
                "tags": "uniquetoken",
            },
            format="json",
        )
        chat = self.client.post(
            "/api/v1/manager/agent/chat/",
            {"message": "uniquetoken"},
            format="json",
        )
        assistant = [m for m in chat.data["messages"] if m["role"] == "assistant"][-1]
        self.assertIn("UniqueTokenContent", assistant["content"])
