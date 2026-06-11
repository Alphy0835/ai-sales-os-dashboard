from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from accounts.models import User
from ai.models import AgentChatMessage, AgentChatSession
from ai.services.agent_prompts import (
    AGENT_SYSTEM_PROMPT,
    CONTEXT_EMPTY,
    DIALOG_HEADER,
    USER_MESSAGE_TEMPLATE,
)
from ai.services.content_guard import strip_delimiter_markers
from ai.services.credentials import llm_available, resolve_ai_config
from ai.services.crm_tools import (
    execute_crm_query,
    format_crm_result,
    maybe_refresh_crm,
)
from ai.services.knowledge import search_knowledge
from ai.services.llm_adapter import LlmAdapterError, chat_completion, parse_json_object
from integrations.services.crm.query import CrmQueryFilters, resolve_tenant_crm_source
from integrations.services.crm_adapter import CrmAdapterError

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 8
LEAD_ID_PATTERN = re.compile(r"\b([A-Za-z]{1,5}\d{2,})\b", re.IGNORECASE)


@dataclass
class AgentPlan:
    crm_search: str | None = None
    crm_stage: str | None = None
    crm_status: str | None = None
    crm_count: bool = False
    kb_query: str | None = None

    def needs_fetch(self) -> bool:
        if self.kb_query:
            return True
        if self.crm_count:
            return True
        return any([self.crm_search, self.crm_stage, self.crm_status])


def _sanitize(value: str) -> str:
    return strip_delimiter_markers(value or "")


def _crm_available(actor: User) -> bool:
    return resolve_tenant_crm_source(actor) is not None


def build_system_prompt(actor: User) -> str:
    tenant_name = actor.tenant.name if actor.tenant_id else "—"
    prompt = (
        AGENT_SYSTEM_PROMPT.replace("{manager_full_name}", actor.full_name or actor.email).replace(
            "{tenant_name}", tenant_name
        )
    )
    if not _crm_available(actor):
        prompt += "\n\nCRM сейчас недоступен — не запрашивай блок crm."
    return prompt


def build_user_content(
    *,
    user_message: str,
    client_name: str,
    client_note: str,
    context_block: str,
    dialog_messages: list[AgentChatMessage] | None = None,
) -> str:
    parts: list[str] = []
    if dialog_messages:
        lines = []
        for msg in dialog_messages[-MAX_HISTORY_MESSAGES:]:
            label = "Менеджер" if msg.role == AgentChatMessage.Role.USER else "Ты"
            lines.append(f"- {label}: {msg.content[:500]}")
        if lines:
            parts.append(f"{DIALOG_HEADER}\n" + "\n".join(lines))

    parts.append(
        USER_MESSAGE_TEMPLATE.format(
            context_block=context_block or CONTEXT_EMPTY,
            user_message=_sanitize(user_message),
            client_name=_sanitize(client_name) or "—",
            client_note=_sanitize(client_note) or "—",
        )
    )
    return "\n\n".join(parts)


def _history_to_messages(dialog_messages: list[AgentChatMessage] | None) -> list[dict]:
    if not dialog_messages:
        return []
    out: list[dict] = []
    for msg in dialog_messages[-MAX_HISTORY_MESSAGES:]:
        role = "user" if msg.role == AgentChatMessage.Role.USER else "assistant"
        out.append({"role": role, "content": msg.content})
    return out


def looks_like_json_plan(raw: str) -> bool:
    return raw.strip().startswith("{")


def parse_agent_plan(raw: str) -> AgentPlan | None:
    try:
        data = parse_json_object(raw)
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None

    crm = data.get("crm") or {}
    kb = data.get("kb") or {}
    if crm and not isinstance(crm, dict):
        crm = {}
    if kb and not isinstance(kb, dict):
        kb = {}

    search = crm.get("search")
    if search is not None:
        search = str(search).strip() or None

    stage = crm.get("stage")
    if stage is not None:
        stage = str(stage).strip() or None

    status = crm.get("status")
    if status is not None:
        status = str(status).strip() or None

    kb_query = kb.get("query")
    if kb_query is not None:
        kb_query = str(kb_query).strip() or None

    return AgentPlan(
        crm_search=search,
        crm_stage=stage,
        crm_status=status,
        crm_count=bool(crm.get("count")),
        kb_query=kb_query,
    )


def emergency_plan_from_message(message: str) -> AgentPlan | None:
    msg = message.lower()
    id_match = LEAD_ID_PATTERN.search(message)
    if id_match:
        return AgentPlan(crm_search=id_match.group(1))
    if "сколько" in msg and ("crm" in msg or "клиент" in msg):
        return AgentPlan(crm_count=True)
    if "gamma" in msg:
        return AgentPlan(crm_search="Gamma")
    return None


def _format_as_of(as_of) -> str:
    if as_of is None:
        return ""
    from django.utils import timezone

    if timezone.is_naive(as_of):
        as_of = timezone.make_aware(as_of)
    local = timezone.localtime(as_of)
    return f"Данные на {local.strftime('%d.%m.%Y %H:%M')}."


def execute_plan(actor: User, plan: AgentPlan) -> tuple[str, list[dict]]:
    sections: list[str] = []
    sources: list[dict] = []

    crm_requested = plan.crm_count or plan.crm_search or plan.crm_stage or plan.crm_status
    if crm_requested:
        if not _crm_available(actor):
            sections.append("--- CRM ---\nCRM недоступен.")
        else:
            try:
                maybe_refresh_crm(actor)
                mode = "count" if plan.crm_count else "list"
                filters = CrmQueryFilters(
                    search=plan.crm_search,
                    pipeline_stage=plan.crm_stage,
                    status_stage=plan.crm_status,
                )
                result = execute_crm_query(actor, filters, mode=mode)
                body = format_crm_result(result, mode)
                as_of = _format_as_of(result.get("as_of"))
                if as_of:
                    body = f"{body}\n{as_of}"
                sections.append(f"--- CRM ---\n{body}")
            except CrmAdapterError as exc:
                logger.warning("CRM plan execution failed: %s", exc)
                sections.append(f"--- CRM ---\nCRM временно недоступен: {exc}")

    if plan.kb_query:
        articles, restricted = search_knowledge(actor, plan.kb_query, include_restricted_hint=False)
        if articles:
            lines = [
                f"• [{a.category}] {a.title}: {a.content[:300]}"
                for a in articles[:5]
            ]
            sections.append("--- БАЗА ЗНАНИЙ ---\n" + "\n".join(lines))
            sources = [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "category": a.category,
                    "excerpt": a.content[:160],
                }
                for a in articles
            ]
        else:
            hint = ""
            if restricted:
                hint = " (есть материалы без доступа по правам)"
            sections.append(f"--- БАЗА ЗНАНИЙ ---\nПо запросу «{plan.kb_query}» статей не найдено{hint}.")

    if not sections:
        return CONTEXT_EMPTY, sources
    return "\n\n".join(sections), sources


def _call_llm(*, actor: User, messages: list[dict]) -> str:
    config = resolve_ai_config(actor)
    return chat_completion(messages=messages, config=config, content_guard=False, temperature=0.2)


def _rule_based_fallback(
    actor: User,
    message: str,
    *,
    client_name: str,
    client_note: str,
) -> tuple[str, list[dict], list[str]]:
    articles, restricted = search_knowledge(actor, message, include_restricted_hint=True)
    sources = [
        {
            "id": str(a.id),
            "title": a.title,
            "category": a.category,
            "excerpt": a.content[:160],
        }
        for a in articles
    ]
    warnings: list[str] = []
    if restricted:
        titles = ", ".join(a.title for a in restricted)
        warnings.append(f"Часть материалов недоступна по вашим правам: {titles}.")

    if not articles and not client_note:
        if restricted:
            return (
                "Материалы по запросу найдены, но недоступны по вашим правам доступа.",
                [],
                warnings,
            )
        return (
            "В базе знаний пока нет материалов по этому запросу. Добавьте их в Настройках → База знаний.",
            [],
            warnings,
        )

    intro = (
        "Стратегия для руководителя на основе базы знаний:"
        if actor.role == User.Role.MANAGER
        else "На основе базы знаний рекомендую:"
    )
    bullets = [f"- {a.title}: {a.content[:120]}..." for a in articles[:3]]
    if not bullets and client_note:
        bullets.append("- Учитывая комментарий, сфокусируйтесь на следующем шаге с клиентом.")
    reply = intro + "\n" + "\n".join(bullets)
    if warnings:
        reply += "\n\n" + " ".join(warnings)
    return reply, sources, warnings


def run_agent_turn(
    *,
    actor: User,
    message: str,
    client_name: str = "",
    client_note: str = "",
    dialog_messages: list[AgentChatMessage] | None = None,
) -> tuple[str, list[dict], list[str]]:
    config = resolve_ai_config(actor)
    system = build_system_prompt(actor)

    if not llm_available(config):
        plan = emergency_plan_from_message(message)
        if plan and plan.needs_fetch():
            context, sources = execute_plan(actor, plan)
            if context != CONTEXT_EMPTY and context.startswith("--- CRM ---"):
                crm_body = context.replace("--- CRM ---\n", "", 1)
                return crm_body, sources, []
        return _rule_based_fallback(actor, message, client_name=client_name, client_note=client_note)

    user_content = build_user_content(
        user_message=message,
        client_name=client_name,
        client_note=client_note,
        context_block=CONTEXT_EMPTY,
        dialog_messages=dialog_messages,
    )
    messages: list[dict] = [{"role": "system", "content": system}]
    messages.extend(_history_to_messages(dialog_messages))
    messages.append({"role": "user", "content": user_content})

    try:
        first = _call_llm(actor=actor, messages=messages)
    except LlmAdapterError as exc:
        logger.warning("Agent plan LLM failed: %s", exc)
        plan = emergency_plan_from_message(message)
        if plan and plan.needs_fetch():
            context, sources = execute_plan(actor, plan)
            if context != CONTEXT_EMPTY:
                return context.replace("--- CRM ---\n", "", 1) if context.startswith("--- CRM ---") else context, sources, []
        return _rule_based_fallback(actor, message, client_name=client_name, client_note=client_note)

    if not looks_like_json_plan(first):
        return first.strip(), [], []

    plan = parse_agent_plan(first)
    if plan is None:
        plan = emergency_plan_from_message(message)
    if plan is None or not plan.needs_fetch():
        return first.strip() or "Не удалось разобрать запрос.", [], []

    context, sources = execute_plan(actor, plan)

    follow_up_user = build_user_content(
        user_message=message,
        client_name=client_name,
        client_note=client_note,
        context_block=context,
        dialog_messages=None,
    )
    follow_messages: list[dict] = [{"role": "system", "content": system}]
    follow_messages.extend(_history_to_messages(dialog_messages))
    follow_messages.append({"role": "user", "content": user_content})
    follow_messages.append({"role": "assistant", "content": first.strip()})
    follow_messages.append({"role": "user", "content": follow_up_user})

    try:
        reply = _call_llm(actor=actor, messages=follow_messages)
        return reply.strip(), sources, []
    except LlmAdapterError as exc:
        logger.warning("Agent answer LLM failed: %s", exc)
        if context != CONTEXT_EMPTY:
            return context, sources, []
        return _rule_based_fallback(actor, message, client_name=client_name, client_note=client_note)
