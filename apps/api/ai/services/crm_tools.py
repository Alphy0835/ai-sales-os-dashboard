from __future__ import annotations

import logging
import re

from accounts.models import User
from ai.services.content_guard import check_user_content
from ai.services.credentials import llm_available, resolve_ai_config
from ai.services.llm_adapter import LlmAdapterError, chat_completion, parse_json_object
from integrations.models import IntegrationSource
from integrations.services.crm.query import CrmQueryFilters, query_crm_leads, resolve_vocabulary
from integrations.tasks import should_sync_source, trigger_tenant_crm_sync

logger = logging.getLogger(__name__)

CRM_KEYWORDS = (
    "сколько",
    "клиент",
    "дожат",
    "менеджер",
    "этап",
    "статус",
    "покажи",
    "список",
)


def _tenant_crm_source(actor: User) -> IntegrationSource | None:
    return (
        IntegrationSource.objects.filter(
            tenant_id=actor.tenant_id,
            is_enabled=True,
            source_type=IntegrationSource.SourceType.CRM,
        )
        .order_by("-last_sync_at")
        .first()
    )


def _has_crm_keywords(message: str) -> bool:
    msg = message.lower()
    return any(kw in msg for kw in CRM_KEYWORDS)


def _rule_based_filters(message: str, source: IntegrationSource | None) -> tuple[CrmQueryFilters, str]:
    msg = message.lower()
    mode = "count" if "сколько" in msg else "list"
    filters = CrmQueryFilters()

    stage_match = re.search(r"этап[еу]?\s+(\S+)", msg)
    if stage_match:
        term = stage_match.group(1)
        if source:
            term = resolve_vocabulary(source, "stages", term)
        filters.pipeline_stage = term
    elif "дожат" in msg:
        filters.pipeline_stage = "дожатие" if source is None else resolve_vocabulary(source, "stages", "дожатие")

    status_match = re.search(r"статус[еу]?\s+(\S+)", msg)
    if status_match:
        term = status_match.group(1)
        if source:
            term = resolve_vocabulary(source, "statuses", term)
        filters.status_stage = term

    manager_match = re.search(r"менеджер[а]?\s+(\S+@\S+)", msg)
    if manager_match:
        filters.manager_email = manager_match.group(1)

    client_match = re.search(r"клиент[а]?\s+([^\s,?]+)", msg)
    if client_match and "сколько" not in msg:
        filters.search = client_match.group(1)

    if "разбор" in msg or "review" in msg:
        filters.needs_review = True

    return filters, mode


def _llm_extract_filters(message: str, actor: User, source: IntegrationSource | None) -> tuple[CrmQueryFilters, str] | None:
    if not check_user_content(message).allowed:
        return None

    config = resolve_ai_config(actor)
    if not llm_available(config):
        return None

    vocabulary = (source.config_json or {}).get("crm_vocabulary", {}) if source else {}
    system = (
        "Extract CRM query filters from the user message. "
        'Return JSON only: {"mode": "list"|"count", "manager_email": null, '
        '"pipeline_stage": null, "status_stage": null, "search": null, "needs_review": null}. '
        f"Use crm_vocabulary aliases when matching stages/statuses: {vocabulary}"
    )
    try:
        raw = chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            config=config,
            temperature=0.0,
        )
        data = parse_json_object(raw)
        filters = CrmQueryFilters(
            manager_email=data.get("manager_email") or None,
            pipeline_stage=data.get("pipeline_stage") or None,
            status_stage=data.get("status_stage") or None,
            search=data.get("search") or None,
            needs_review=data.get("needs_review") if data.get("needs_review") is not None else None,
        )
        mode = data.get("mode", "list")
        if mode not in ("list", "count"):
            mode = "list"
        return filters, mode
    except (LlmAdapterError, ValueError, TypeError) as exc:
        logger.warning("CRM LLM filter extraction failed: %s", exc)
        return None


def _rule_based_is_specific(filters: CrmQueryFilters, mode: str) -> bool:
    if mode == "count":
        return True
    return any(
        [
            filters.pipeline_stage,
            filters.status_stage,
            filters.manager_email,
            filters.search,
            filters.needs_review is not None,
        ]
    )


def detect_crm_intent(message: str, actor: User) -> tuple[bool, CrmQueryFilters | None, str]:
    if not _has_crm_keywords(message):
        return False, None, "list"

    source = _tenant_crm_source(actor)
    filters, mode = _rule_based_filters(message, source)
    if _rule_based_is_specific(filters, mode):
        return True, filters, mode

    llm_result = _llm_extract_filters(message, actor, source)
    if llm_result is not None:
        return True, llm_result[0], llm_result[1]

    return True, filters, mode


def execute_crm_query(actor: User, filters: CrmQueryFilters, mode: str = "list") -> dict:
    source = _tenant_crm_source(actor)
    return query_crm_leads(
        actor,
        filters=filters,
        mode=mode,
        integration_source=source,
    )


def format_crm_result(result: dict, mode: str) -> str:
    if mode == "count":
        return f"В CRM найдено клиентов: {result['count']}."
    if not result.get("leads"):
        return "По запросу клиенты в CRM не найдены."
    lines = [f"Найдено {result['count']} клиент(ов):"]
    for lead in result["leads"][:10]:
        stage = lead.get("pipeline_stage") or "—"
        status = lead.get("status_stage") or "—"
        lines.append(f"- {lead['client_name']} (этап: {stage}, статус: {status})")
    if result["count"] > len(result["leads"]):
        lines.append(f"... и ещё {result['count'] - len(result['leads'])}.")
    return "\n".join(lines)


def maybe_refresh_crm(actor: User, *, force: bool = False) -> bool:
    sources = IntegrationSource.objects.filter(
        tenant_id=actor.tenant_id,
        is_enabled=True,
        source_type=IntegrationSource.SourceType.CRM,
        config_json__provider="google_sheets",
    ).exclude(credentials_encrypted="")
    stale = [s for s in sources if should_sync_source(s, force=force)]
    if not stale:
        return False
    trigger_tenant_crm_sync.delay(str(actor.tenant_id), force=force)
    return True
