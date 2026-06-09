from django.db.models import Q

from accounts.models import ManagerScope, User, Workspace


def get_scoped_workspace_ids(user) -> set:
    if user.role == User.Role.EMPLOYEE:
        if user.workspace_id:
            return {user.workspace_id}
        return set()
    return set(
        ManagerScope.objects.filter(user=user).values_list("workspace_id", flat=True)
    )


def get_scoped_workspaces(user):
    workspace_ids = get_scoped_workspace_ids(user)
    if not workspace_ids:
        return Workspace.objects.none()
    return Workspace.objects.filter(id__in=workspace_ids, tenant_id=user.tenant_id, is_active=True)


def is_subordinate_manager(actor: User, target: User) -> bool:
    if target.role != User.Role.MANAGER:
        return False
    current = target
    while current.manager_id:
        if current.manager_id == actor.id:
            return True
        current = current.manager
    return False


def user_in_scope(actor: User, target: User) -> bool:
    if actor.tenant_id != target.tenant_id or not target.is_active:
        return False
    if actor.id == target.id:
        return True
    if actor.role == User.Role.EMPLOYEE:
        return False

    scoped_ws = get_scoped_workspace_ids(actor)
    if not scoped_ws:
        return False

    if target.role == User.Role.EMPLOYEE:
        return target.workspace_id in scoped_ws

    if not is_subordinate_manager(actor, target):
        return False
    target_ws = get_scoped_workspace_ids(target)
    return bool(target_ws) and target_ws.issubset(scoped_ws)


def get_accessible_users(actor: User):
    if actor.role == User.Role.EMPLOYEE:
        return User.objects.filter(id=actor.id, tenant_id=actor.tenant_id, is_active=True)

    scoped_ws = get_scoped_workspace_ids(actor)
    if not scoped_ws:
        return User.objects.none()

    employees = Q(
        role=User.Role.EMPLOYEE,
        workspace_id__in=scoped_ws,
    )
    sub_managers = Q(role=User.Role.MANAGER, manager__isnull=False)
    candidates = User.objects.filter(
        tenant_id=actor.tenant_id,
        is_active=True,
    ).filter(employees | sub_managers).select_related("workspace", "manager").distinct()

    return [u for u in candidates if user_in_scope(actor, u)]
