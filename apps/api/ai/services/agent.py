import logging

from accounts.models import User
from ai.models import AgentChatMessage, AgentChatSession
from ai.services.credentials import llm_available, resolve_ai_config
from ai.services.knowledge import search_knowledge
from ai.services.llm_adapter import LlmAdapterError, chat_completion
from integrations.models import Transcription
from integrations.services.scope import recordings_queryset

logger = logging.getLogger(__name__)


def _recording_context(actor: User, client_name: str) -> str:
    if not client_name:
        return ""
    qs = recordings_queryset(actor).filter(client_name__icontains=client_name)
    lines = []
    for rec in qs[:3]:
        if hasattr(rec, "transcription") and rec.transcription.status == Transcription.Status.COMPLETED:
            lines.append(f"Запись {rec.client_name}: {rec.transcription.text[:200]}...")
    return "\n".join(lines)


def _rule_based_reply(
    *,
    actor: User,
    articles,
    restricted,
    client_name: str,
    client_note: str,
    recording_ctx: str,
    warnings: list[str],
) -> tuple[str, list[dict], list[str]]:
    sources = [
        {
            "id": str(a.id),
            "title": a.title,
            "category": a.category,
            "excerpt": a.content[:160],
        }
        for a in articles
    ]

    if not articles and not recording_ctx and not client_note:
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

    answer_intro = "На основе базы знаний и контекста рекомендую:"
    if actor.role == User.Role.MANAGER:
        answer_intro = "Стратегия для руководителя на основе RAG и контекста:"

    bullet_points = []
    for article in articles[:3]:
        bullet_points.append(f"- {article.title}: {article.content[:120]}...")
    if not bullet_points and client_note:
        bullet_points.append("- Учитывая комментарий, сфокусируйтесь на следующем шаге с клиентом.")

    reply = answer_intro + "\n" + "\n".join(bullet_points)
    if warnings:
        reply += "\n\n" + " ".join(warnings)
    return reply, sources, warnings


def generate_agent_reply(
    *,
    actor: User,
    message: str,
    client_name: str = "",
    client_note: str = "",
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

    recording_ctx = _recording_context(actor, client_name)

    config = resolve_ai_config(actor)
    if llm_available(config):
        kb_block = "\n\n".join(f"• {a.title}: {a.content[:500]}" for a in articles[:5])
        system = (
            "Ты AI-ассистент отдела продаж. Отвечай на русском, кратко и по делу. "
            "Используй только предоставленный контекст базы знаний и записей разговоров."
        )
        user_content = f"Запрос: {message}\n"
        if client_name:
            user_content += f"Клиент: {client_name}\n"
        if client_note:
            user_content += f"Комментарий: {client_note}\n"
        if recording_ctx:
            user_content += f"Записи:\n{recording_ctx}\n"
        if kb_block:
            user_content += f"База знаний:\n{kb_block}\n"
        try:
            reply = chat_completion(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                config=config,
            )
            if warnings:
                reply += "\n\n" + " ".join(warnings)
            return reply, sources, warnings
        except LlmAdapterError as exc:
            logger.warning("LLM agent fallback: %s", exc)

    return _rule_based_reply(
        actor=actor,
        articles=articles,
        restricted=restricted,
        client_name=client_name,
        client_note=client_note,
        recording_ctx=recording_ctx,
        warnings=warnings,
    )


def chat_with_agent(
    *,
    actor: User,
    message: str,
    session_id: str | None = None,
    client_name: str = "",
    client_note: str = "",
) -> AgentChatSession:
    agent_role = (
        AgentChatSession.AgentRole.MANAGER
        if actor.role == User.Role.MANAGER
        else AgentChatSession.AgentRole.EMPLOYEE
    )

    if session_id:
        session = AgentChatSession.objects.filter(
            id=session_id, tenant_id=actor.tenant_id, user=actor
        ).first()
        if session is None:
            raise AgentChatSession.DoesNotExist("Session not found")
    else:
        session = AgentChatSession.objects.create(
            tenant=actor.tenant,
            user=actor,
            agent_role=agent_role,
            client_name=client_name,
            client_note=client_note,
        )

    if client_name:
        session.client_name = client_name
    if client_note:
        session.client_note = client_note
    session.save()

    reply, sources, _ = generate_agent_reply(
        actor=actor,
        message=message,
        client_name=session.client_name,
        client_note=session.client_note,
    )

    AgentChatMessage.objects.create(session=session, role=AgentChatMessage.Role.USER, content=message)
    AgentChatMessage.objects.create(
        session=session,
        role=AgentChatMessage.Role.ASSISTANT,
        content=reply,
        sources=sources,
    )
    return session
