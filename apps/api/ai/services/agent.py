import logging

from accounts.models import User
from ai.models import AgentChatMessage, AgentChatSession
from ai.services.agent_orchestrator import run_agent_turn
from ai.services.content_guard import validate_agent_fields

logger = logging.getLogger(__name__)


def generate_agent_reply(
    *,
    actor: User,
    message: str,
    client_name: str = "",
    client_note: str = "",
    dialog_messages: list[AgentChatMessage] | None = None,
) -> tuple[str, list[dict], list[str]]:
    guard = validate_agent_fields(message=message, client_name=client_name, client_note=client_note)
    if not guard.allowed:
        return guard.block_message, [], []

    return run_agent_turn(
        actor=actor,
        message=message,
        client_name=client_name,
        client_note=client_note,
        dialog_messages=dialog_messages,
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

    history = list(session.messages.order_by("created_at"))
    reply, sources, _ = generate_agent_reply(
        actor=actor,
        message=message,
        client_name=session.client_name,
        client_note=session.client_note,
        dialog_messages=history,
    )

    AgentChatMessage.objects.create(session=session, role=AgentChatMessage.Role.USER, content=message)
    AgentChatMessage.objects.create(
        session=session,
        role=AgentChatMessage.Role.ASSISTANT,
        content=reply,
        sources=sources,
    )
    return session
