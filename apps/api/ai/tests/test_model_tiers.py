from django.test import TestCase, override_settings

from accounts.models import Tenant, User, Workspace
from ai.models import ModelTier, TenantAiConfig, WorkspaceAiConfig
from ai.services.credentials import resolve_ai_config
from ai.services.model_tiers import TIER_PRESETS, resolve_models


class ResolveModelsTestCase(TestCase):
    def test_standard_tier_preset(self):
        tenant_cfg = TenantAiConfig(model_tier=ModelTier.STANDARD)
        chat, embedding = resolve_models(
            tenant_cfg,
            None,
            fallback_chat="env/chat",
            fallback_embedding="env/embed",
        )
        self.assertEqual(chat, TIER_PRESETS[ModelTier.STANDARD]["chat_model"])
        self.assertEqual(embedding, TIER_PRESETS[ModelTier.STANDARD]["embedding_model"])

    def test_free_tier_falls_back_embedding_to_env(self):
        tenant_cfg = TenantAiConfig(model_tier=ModelTier.FREE)
        chat, embedding = resolve_models(
            tenant_cfg,
            None,
            fallback_chat="env/chat",
            fallback_embedding="env/embed",
        )
        self.assertEqual(chat, TIER_PRESETS[ModelTier.FREE]["chat_model"])
        self.assertEqual(embedding, "env/embed")

    def test_premium_tier_preset(self):
        tenant_cfg = TenantAiConfig(model_tier=ModelTier.PREMIUM)
        chat, embedding = resolve_models(
            tenant_cfg,
            None,
            fallback_chat="env/chat",
            fallback_embedding="env/embed",
        )
        self.assertEqual(chat, "openai/gpt-4o")
        self.assertEqual(embedding, "openai/text-embedding-3-small")

    def test_workspace_tier_overrides_tenant(self):
        tenant_cfg = TenantAiConfig(model_tier=ModelTier.STANDARD)
        workspace_cfg = WorkspaceAiConfig(model_tier=ModelTier.PREMIUM)
        chat, embedding = resolve_models(
            tenant_cfg,
            workspace_cfg,
            fallback_chat="env/chat",
            fallback_embedding="env/embed",
        )
        self.assertEqual(chat, TIER_PRESETS[ModelTier.PREMIUM]["chat_model"])
        self.assertEqual(embedding, TIER_PRESETS[ModelTier.PREMIUM]["embedding_model"])

    def test_workspace_inherits_tenant_tier_when_blank(self):
        tenant_cfg = TenantAiConfig(model_tier=ModelTier.FREE)
        workspace_cfg = WorkspaceAiConfig(model_tier="")
        chat, _ = resolve_models(
            tenant_cfg,
            workspace_cfg,
            fallback_chat="env/chat",
            fallback_embedding="env/embed",
        )
        self.assertEqual(chat, TIER_PRESETS[ModelTier.FREE]["chat_model"])

    def test_advanced_override_wins_over_tier(self):
        tenant_cfg = TenantAiConfig(
            model_tier=ModelTier.STANDARD,
            chat_model="custom/chat",
            embedding_model="custom/embed",
        )
        chat, embedding = resolve_models(
            tenant_cfg,
            None,
            fallback_chat="env/chat",
            fallback_embedding="env/embed",
        )
        self.assertEqual(chat, "custom/chat")
        self.assertEqual(embedding, "custom/embed")

    def test_workspace_advanced_override_wins(self):
        tenant_cfg = TenantAiConfig(model_tier=ModelTier.STANDARD)
        workspace_cfg = WorkspaceAiConfig(
            model_tier=ModelTier.PREMIUM,
            chat_model="workspace/chat",
        )
        chat, embedding = resolve_models(
            tenant_cfg,
            workspace_cfg,
            fallback_chat="env/chat",
            fallback_embedding="env/embed",
        )
        self.assertEqual(chat, "workspace/chat")
        self.assertEqual(embedding, TIER_PRESETS[ModelTier.PREMIUM]["embedding_model"])


@override_settings(
    OPENROUTER_API_KEY="test-key",
    LLM_CHAT_MODEL="env/gpt-default",
    LLM_EMBEDDING_MODEL="env/embed-default",
)
class ResolveAiConfigTierTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tier Co", slug="tier-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="ОП")
        self.user = User.objects.create_user(
            email="mgr@tier.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )

    def test_tenant_standard_tier_applied(self):
        TenantAiConfig.objects.create(tenant=self.tenant, model_tier=ModelTier.STANDARD)
        config = resolve_ai_config(self.user)
        self.assertEqual(config.chat_model, "openai/gpt-4o-mini")
        self.assertEqual(config.embedding_model, "openai/text-embedding-3-small")
        self.assertEqual(config.source, "tenant")

    def test_workspace_premium_overrides_tenant_standard(self):
        TenantAiConfig.objects.create(tenant=self.tenant, model_tier=ModelTier.STANDARD)
        WorkspaceAiConfig.objects.create(workspace=self.workspace, model_tier=ModelTier.PREMIUM)
        config = resolve_ai_config(self.user)
        self.assertEqual(config.chat_model, "openai/gpt-4o")
        self.assertEqual(config.source, "workspace")

    def test_free_tier_uses_env_embedding_fallback(self):
        TenantAiConfig.objects.create(tenant=self.tenant, model_tier=ModelTier.FREE)
        config = resolve_ai_config(self.user)
        self.assertEqual(config.chat_model, "meta-llama/llama-3.3-70b-instruct:free")
        self.assertEqual(config.embedding_model, "env/embed-default")

    def test_advanced_override_in_resolve_ai_config(self):
        TenantAiConfig.objects.create(
            tenant=self.tenant,
            model_tier=ModelTier.STANDARD,
            chat_model="override/chat",
        )
        config = resolve_ai_config(self.user)
        self.assertEqual(config.chat_model, "override/chat")
        self.assertEqual(config.embedding_model, "openai/text-embedding-3-small")
