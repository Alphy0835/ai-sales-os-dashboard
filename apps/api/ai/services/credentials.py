from dataclasses import dataclass

from django.conf import settings

from accounts.models import User
from ai.models import TenantAiConfig, WorkspaceAiConfig
from ai.services.crypto import decrypt_secret


@dataclass(frozen=True)
class AiConfig:
    api_key: str
    base_url: str
    chat_model: str
    embedding_model: str
    embedding_dimensions: int
    is_enabled: bool
    source: str


def _from_env() -> AiConfig:
    return AiConfig(
        api_key=getattr(settings, "OPENROUTER_API_KEY", "") or "",
        base_url=getattr(settings, "LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        chat_model=getattr(settings, "LLM_CHAT_MODEL", "openai/gpt-4o-mini"),
        embedding_model=getattr(settings, "LLM_EMBEDDING_MODEL", "openai/text-embedding-3-small"),
        embedding_dimensions=int(getattr(settings, "LLM_EMBEDDING_DIMENSIONS", 1536)),
        is_enabled=bool(getattr(settings, "OPENROUTER_API_KEY", "") or ""),
        source="env",
    )


def _merge_config(*, base: AiConfig, tenant_cfg: TenantAiConfig | None, workspace_cfg: WorkspaceAiConfig | None) -> AiConfig:
    api_key = base.api_key
    base_url = base.base_url
    chat_model = base.chat_model
    embedding_model = base.embedding_model
    is_enabled = base.is_enabled
    source = base.source

    if tenant_cfg:
        if tenant_cfg.api_key_encrypted:
            decrypted = decrypt_secret(tenant_cfg.api_key_encrypted)
            if decrypted:
                api_key = decrypted
        if tenant_cfg.base_url:
            base_url = tenant_cfg.base_url
        if tenant_cfg.chat_model:
            chat_model = tenant_cfg.chat_model
        if tenant_cfg.embedding_model:
            embedding_model = tenant_cfg.embedding_model
        is_enabled = tenant_cfg.is_enabled
        source = "tenant"

    if workspace_cfg:
        if workspace_cfg.api_key_encrypted:
            decrypted = decrypt_secret(workspace_cfg.api_key_encrypted)
            if decrypted:
                api_key = decrypted
        if workspace_cfg.base_url:
            base_url = workspace_cfg.base_url
        if workspace_cfg.chat_model:
            chat_model = workspace_cfg.chat_model
        if workspace_cfg.embedding_model:
            embedding_model = workspace_cfg.embedding_model
        if workspace_cfg.is_enabled is not None:
            is_enabled = workspace_cfg.is_enabled
        source = "workspace"

    return AiConfig(
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        chat_model=chat_model,
        embedding_model=embedding_model,
        embedding_dimensions=base.embedding_dimensions,
        is_enabled=is_enabled and bool(api_key),
        source=source,
    )


def resolve_ai_config(actor: User) -> AiConfig:
    base = _from_env()
    tenant_cfg = TenantAiConfig.objects.filter(tenant_id=actor.tenant_id).first()
    workspace_cfg = None
    if actor.workspace_id:
        workspace_cfg = WorkspaceAiConfig.objects.filter(workspace_id=actor.workspace_id).first()
    return _merge_config(base=base, tenant_cfg=tenant_cfg, workspace_cfg=workspace_cfg)


def llm_available(config: AiConfig) -> bool:
    return config.is_enabled and bool(config.api_key)
