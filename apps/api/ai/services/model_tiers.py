from ai.models import ModelTier, TenantAiConfig, WorkspaceAiConfig

TIER_PRESETS: dict[str, dict[str, str]] = {
    ModelTier.FREE: {
        "chat_model": "google/gemma-4-31b-it:free",
        "embedding_model": "",
    },
    ModelTier.STANDARD: {
        "chat_model": "openai/gpt-4o-mini",
        "embedding_model": "openai/text-embedding-3-small",
    },
    ModelTier.PREMIUM: {
        "chat_model": "openai/gpt-4o",
        "embedding_model": "openai/text-embedding-3-small",
    },
}


def _effective_tier(
    tenant_cfg: TenantAiConfig | None,
    workspace_cfg: WorkspaceAiConfig | None,
) -> str:
    if workspace_cfg and workspace_cfg.model_tier:
        return workspace_cfg.model_tier
    if tenant_cfg and tenant_cfg.model_tier:
        return tenant_cfg.model_tier
    return ""


def resolve_models(
    tenant_cfg: TenantAiConfig | None,
    workspace_cfg: WorkspaceAiConfig | None,
    *,
    fallback_chat: str,
    fallback_embedding: str,
) -> tuple[str, str]:
    tier = _effective_tier(tenant_cfg, workspace_cfg)
    if tier:
        preset = TIER_PRESETS[tier]
        chat_model = preset["chat_model"] or fallback_chat
        embedding_model = preset["embedding_model"] or fallback_embedding
    else:
        chat_model = fallback_chat
        embedding_model = fallback_embedding

    if tenant_cfg:
        if tenant_cfg.chat_model:
            chat_model = tenant_cfg.chat_model
        if tenant_cfg.embedding_model:
            embedding_model = tenant_cfg.embedding_model

    if workspace_cfg:
        if workspace_cfg.chat_model:
            chat_model = workspace_cfg.chat_model
        if workspace_cfg.embedding_model:
            embedding_model = workspace_cfg.embedding_model

    return chat_model, embedding_model
