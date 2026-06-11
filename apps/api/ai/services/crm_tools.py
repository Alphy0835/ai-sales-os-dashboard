from __future__ import annotations

import logging
import re

from accounts.models import User
from ai.services.content_guard import check_user_content
from ai.services.credentials import llm_available, resolve_ai_config
from ai.services.llm_adapter import LlmAdapterError, chat_completion, parse_json_object
from integrations.models import IntegrationSource
from integrations.services.crm.query import (
    CrmQueryFilters,
    query_crm_leads,
    resolve_tenant_crm_source,
)
from integrations.services.crm_adapter import CrmAdapterError
from integrations.tasks import should_sync_source, trigger_tenant_crm_sync

logger = logging.getLogger(__name__)

_CRM_INTENT_SYSTEM = """You decide whether a sales assistant message requires a CRM database lookup.

Return JSON only:
{
  "needs_crm_query": boolean,
  "mode": "list" | "count",
  "manager_email": string | null,
  "pipeline_stage": string | null,
  "status_stage": string | null,
  "search": string | null,
  "needs_review": boolean | null
}

Set needs_crm_query=true when the user asks to find, count, or list clients/leads/deals in CRM,
including lookup by lead id (e.g. TW26055), client name, pipeline stage, status, or manager.

Set needs_crm_query=false for coaching, scripts, objection handling, or strategy without CRM lookup.
Examples of false: "клиент говорит дорого", "как ему ответить", "помоги со скриптом".

When needs_crm_query=true:
- mode=count for totals ("сколько клиентов", "количество сделок")
- mode=list for named lookups and filtered lists
- search: lead id, client name fragment, phone — never put verbs like "зовут" into search
- needs_review=true only when user explicitly asks about review queue / разбор
- map stage/status terms using crm_vocabulary when provided
"""


def _tenant_crm_source(actor: User) -> IntegrationSource | None:
    return resolve_tenant_crm_source(actor)


def _build_intent_prompt(source: IntegrationSource | None) -> str:
    vocabulary = (source.config_json or {}).get("crm_vocabulary", {}) if source else {}
    return f"{_CRM_INTENT_SYSTEM}\ncrm_vocabulary: {vocabulary}"


def _parse_crm_intent_payload(data: dict) -> tuple[bool, CrmQueryFilters | None, str]:
    needs_crm = bool(data.get("needs_crm_query"))
    if not needs_crm:
        return False, None, "list"

    mode = data.get("mode", "list")
    if mode not in ("list", "count"):
        mode = "list"

    needs_review = data.get("needs_review")
    if needs_review is not None and not isinstance(needs_review, bool):
        needs_review = bool(needs_review)

    filters = CrmQueryFilters(
        manager_email=data.get("manager_email") or None,
        pipeline_stage=data.get("pipeline_stage") or None,
        status_stage=data.get("status_stage") or None,
        search=data.get("search") or None,
        needs_review=needs_review,
    )
    return True, filters, mode


def _llm_classify_crm_intent(
    message: str,
    actor: User,
    source: IntegrationSource | None,
) -> tuple[bool, CrmQueryFilters | None, str] | None:
    if not check_user_content(message).allowed:
        return False, None, "list"

    config = resolve_ai_config(actor)
    if not llm_available(config):
        return None

    try:
        raw = chat_completion(
            messages=[
                {"role": "system", "content": _build_intent_prompt(source)},
                {"role": "user", "content": message},
            ],
            config=config,
            temperature=0.0,
        )
        data = parse_json_object(raw)
        return _parse_crm_intent_payload(data)
    except (LlmAdapterError, ValueError, TypeError) as exc:
        logger.warning("CRM LLM intent classification failed: %s", exc)
        return None


def _emergency_crm_intent_fallback(message: str) -> tuple[bool, CrmQueryFilters | None, str] | None:
    """Only when LLM is unavailable (rate limit, outage). Not the primary router."""
    msg = message.lower()
    id_match = re.search(r"\b([A-Za-z]{1,5}\d{2,})\b", message, re.IGNORECASE)
    if id_match:
        return True, CrmQueryFilters(search=id_match.group(1)), "list"
    if "сколько" in msg and ("crm" in msg or "клиент" in msg):
        return True, CrmQueryFilters(), "count"
    return None


def detect_crm_intent(message: str, actor: User) -> tuple[bool, CrmQueryFilters | None, str]:
    source = _tenant_crm_source(actor)
    llm_result = _llm_classify_crm_intent(message, actor, source)
    if llm_result is not None:
        return llm_result

    fallback = _emergency_crm_intent_fallback(message)
    if fallback is not None:
        logger.info("CRM intent emergency fallback for actor %s", actor.id)
        return fallback

    logger.info("CRM intent skipped: LLM unavailable for actor %s", actor.id)
    return False, None, "list"


def execute_crm_query(actor: User, filters: CrmQueryFilters, mode: str = "list") -> dict:
    source = _tenant_crm_source(actor)
    return query_crm_leads(
        actor,
        filters=filters,
        mode=mode,
        integration_source=source,
    )


def _format_lead_details(lead: dict, *, bullet: str = "") -> str:
    stage = lead.get("pipeline_stage") or "—"
    status = lead.get("status_stage") or "—"
    lead_ref = lead.get("external_lead_id") or lead.get("client_name")
    lines = [
        f"{bullet}Клиент {lead_ref}: {lead['client_name']} "
        f"(этап: {stage}, статус: {status})"
    ]
    phone = (lead.get("phone") or "").strip()
    if phone:
        lines.append(f"{bullet}  тел: {phone}")
    city = (lead.get("city") or "").strip()
    if city:
        lines.append(f"{bullet}  город: {city}")
    comment = (lead.get("communication_comment") or "").strip()
    lines.append(f"{bullet}  комментарий: {comment or '—'}")
    return "\n".join(lines)


def format_crm_result(result: dict, mode: str) -> str:
    if mode == "count":
        return f"В CRM найдено клиентов: {result['count']}."
    if not result.get("leads"):
        return "По запросу клиенты в CRM не найдены."
    if len(result["leads"]) == 1:
        return _format_lead_details(result["leads"][0])
    lines = [f"Найдено {result['count']} клиент(ов):"]
    for lead in result["leads"][:10]:
        lines.append(_format_lead_details(lead, bullet="- "))
    if result["count"] > len(result["leads"]):
        lines.append(f"... и ещё {result['count'] - len(result['leads'])}.")
    return "\n".join(lines)


def maybe_refresh_crm(actor: User, *, force: bool = False) -> bool:
    """Queue CRM sync for non-Sheets sources only. Google Sheets agent reads live."""
    sources = IntegrationSource.objects.filter(
        tenant_id=actor.tenant_id,
        is_enabled=True,
        source_type=IntegrationSource.SourceType.CRM,
    ).exclude(credentials_encrypted="").exclude(config_json__provider="google_sheets")
    stale = [s for s in sources if should_sync_source(s, force=force)]
    if not stale:
        return False
    trigger_tenant_crm_sync.delay(str(actor.tenant_id), force=force)
    return True
