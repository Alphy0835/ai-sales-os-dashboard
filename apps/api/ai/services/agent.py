from accounts.models import User
from ai.models import AgentChatMessage, AgentChatSession
from ai.services.knowledge import search_knowledge
from integrations.models import ConversationRecording, Transcription


def _recording_context(actor: User, client_name: str) -> str:
    if not client_name:
        return ""
    qs = ConversationRecording.objects.filter(
        tenant_id=actor.tenant_id,
        client_name__icontains=client_name,
    ).select_related("transcription", "employee")
    if actor.role == User.Role.EMPLOYEE:
        qs = qs.filter(employee=actor)
    lines = []
    for rec in qs[:3]:
        if hasattr(rec, "transcription") and rec.transcription.status == Transcription.Status.COMPLETED:
            lines.append(f"Запись {rec.client_name}: {rec.transcription.text[:200]}...")
    return "\n".join(lines)


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

    parts = []
    if client_name:
        parts.append(f"Контекст клиента: {client_name}.")
    if client_note:
        parts.append(f"Комментарий: {client_note}")
    if recording_ctx:
        parts.append(f"Записи общения:\n{recording_ctx}")

    if articles:
        kb = "\n\n".join(f"• {a.title}: {a.content[:300]}" for a in articles[:3])
        parts.append(f"Материалы базы знаний:\n{kb}")

    answer_intro = "На основе базы знаний и контекста рекомендую:"
    if actor.role == User.Role.MANAGER:
        answer_intro = "Стратегия для руководителя на основе RAG и контекста:"

    bullet_points = []
    for article in articles[:3]:
        bullet_points.append(f"- {article.title}: {article.content[:120]}...")
    if not bullet_points and client_note:
        bullet_points.append(f"- Учитывая комментарий, сфокусируйтесь на следующем шаге с клиентом.")

    reply = answer_intro + "\n" + "\n".join(bullet_points)
    if warnings:
        reply += "\n\n" + " ".join(warnings)
    return reply, sources, warnings


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
        session = AgentChatSession.objects.get(id=session_id, tenant_id=actor.tenant_id, user=actor)
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
