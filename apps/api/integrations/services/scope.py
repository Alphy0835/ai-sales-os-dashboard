from accounts.models import User
from accounts.services.scope import user_in_scope
from integrations.models import ConversationRecording


def recordings_queryset(actor: User):
    qs = ConversationRecording.objects.filter(tenant_id=actor.tenant_id).select_related(
        "employee",
        "workspace",
        "integration_source",
        "transcription",
    )
    if actor.role == User.Role.EMPLOYEE:
        return qs.filter(employee_id=actor.id)

    from accounts.services.scope import get_accessible_users

    employee_ids = [u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE]
    return qs.filter(employee_id__in=employee_ids)


def can_access_recording(actor: User, recording: ConversationRecording) -> bool:
    if recording.tenant_id != actor.tenant_id:
        return False
    if actor.role == User.Role.EMPLOYEE:
        return recording.employee_id == actor.id
    return user_in_scope(actor, recording.employee)
