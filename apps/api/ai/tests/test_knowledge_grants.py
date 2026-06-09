from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import KnowledgeArticle, KnowledgeArticleGrant
from ai.services.knowledge import article_accessible


class KnowledgeGrantTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="T", slug="t-grant")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="WS")
        self.manager = User.objects.create_user(
            email="mgr-grant@demo.local",
            password="demo1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        self.employee = User.objects.create_user(
            email="emp-grant@demo.local",
            password="demo1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
            manager=self.manager,
        )
        for user, perms in [
            (self.manager, {"settings": "edit", "agent": "use"}),
            (self.employee, {"agent": "use"}),
        ]:
            for module, level in perms.items():
                ModulePermission.objects.create(user=user, module=module, level=level)

        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)

        self.article = KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Manager only",
            content="Secret playbook",
            access_level=KnowledgeArticle.AccessLevel.MANAGER,
        )

        self.client = APIClient()
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": self.manager.email, "password": "demo1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_employee_denied_manager_article_by_default(self):
        self.assertFalse(article_accessible(self.employee, self.article))

    def test_grant_allows_employee_access(self):
        KnowledgeArticleGrant.objects.create(
            tenant=self.tenant,
            user=self.employee,
            article=self.article,
            is_allowed=True,
        )
        self.assertTrue(article_accessible(self.employee, self.article))

    @patch("ai.tasks.embed_knowledge_article.delay")
    def test_knowledge_grant_api_ceiling(self, _mock_embed):
        response = self.client.put(
            f"/api/v1/permissions/users/{self.employee.id}/knowledge/",
            {"grants": [{"article_id": str(self.article.id), "is_allowed": True}]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            KnowledgeArticleGrant.objects.filter(user=self.employee, article=self.article, is_allowed=True).exists()
        )

    @patch("ai.tasks.embed_knowledge_article.delay")
    def test_knowledge_grant_deny_override(self, _mock_embed):
        public = KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Public",
            content="All can read",
            access_level=KnowledgeArticle.AccessLevel.ALL,
        )
        KnowledgeArticleGrant.objects.create(
            tenant=self.tenant,
            user=self.employee,
            article=public,
            is_allowed=False,
        )
        self.assertFalse(article_accessible(self.employee, public))
