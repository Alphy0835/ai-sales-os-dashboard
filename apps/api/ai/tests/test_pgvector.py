from unittest.mock import patch
import unittest

from django.db import connection
from django.test import TestCase

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import KnowledgeArticle
from ai.services.knowledge import search_knowledge
from ai.tasks import embed_knowledge_article


@unittest.skipUnless(connection.vendor == "postgresql", "PostgreSQL required")
class PgvectorTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="PG Co", slug="pg-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@pg.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        ModulePermission.objects.update_or_create(
            user=self.manager,
            module=ModulePermission.Module.AGENT,
            defaults={"level": ModulePermission.Level.USE},
        )

    @patch("ai.tasks.embed_texts")
    def test_embed_knowledge_article_saves_vector(self, mock_embed):
        mock_embed.return_value = [[0.1] * 1536]
        article = KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Vector article",
            category=KnowledgeArticle.Category.PRODUCT,
            content="Unique semantic content for embedding test.",
            access_level=KnowledgeArticle.AccessLevel.ALL,
        )
        embed_knowledge_article(str(article.id))
        article.refresh_from_db()
        self.assertIsNotNone(article.embedding)
        self.assertEqual(article.content_hash, article.compute_content_hash())

    @patch("ai.services.knowledge.embed_texts")
    def test_vector_search_prefers_semantic_match(self, mock_embed):
        mock_embed.return_value = [[1.0] + [0.0] * 1535]
        near = KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Alpha topic",
            category=KnowledgeArticle.Category.PRODUCT,
            content="zzzz",
            access_level=KnowledgeArticle.AccessLevel.ALL,
            embedding=[0.99] + [0.0] * 1535,
        )
        KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Keyword only",
            category=KnowledgeArticle.Category.PRODUCT,
            content="alpha keyword appears here",
            access_level=KnowledgeArticle.AccessLevel.ALL,
        )
        accessible, _ = search_knowledge(self.manager, "semantic query")
        self.assertTrue(accessible)
        self.assertEqual(accessible[0].id, near.id)

    @patch("ai.services.knowledge.embed_texts")
    def test_vector_search_falls_back_on_llm_error(self, mock_embed):
        from ai.services.llm_adapter import LlmAdapterError

        mock_embed.side_effect = LlmAdapterError("no key")
        KnowledgeArticle.objects.create(
            tenant=self.tenant,
            title="Fallback article",
            category=KnowledgeArticle.Category.PRODUCT,
            content="uniquefallbacktoken content",
            access_level=KnowledgeArticle.AccessLevel.ALL,
        )
        accessible, _ = search_knowledge(self.manager, "uniquefallbacktoken")
        self.assertEqual(len(accessible), 1)
