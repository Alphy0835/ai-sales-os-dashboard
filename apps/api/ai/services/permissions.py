from accounts.models import ModulePermission, User
from accounts.services.permissions import get_user_permissions
from accounts.services.scope import get_scoped_workspaces, user_in_scope
from ai.models import QualityCriterion


def settings_permission_level(user) -> str:
    return get_user_permissions(user).get(ModulePermission.Module.SETTINGS, ModulePermission.Level.NONE)


def analytics_permission_level(user) -> str:
    return get_user_permissions(user).get(ModulePermission.Module.ANALYTICS, ModulePermission.Level.NONE)


def can_view_criteria(user) -> bool:
    return settings_permission_level(user) != ModulePermission.Level.NONE


def can_edit_criteria(user) -> bool:
    return settings_permission_level(user) == ModulePermission.Level.EDIT


def can_view_reports(user) -> bool:
    return analytics_permission_level(user) in (
        ModulePermission.Level.VIEW,
        ModulePermission.Level.RUN,
        ModulePermission.Level.EDIT,
    )


def can_run_reports(user) -> bool:
    return analytics_permission_level(user) in (
        ModulePermission.Level.RUN,
        ModulePermission.Level.EDIT,
    )


def criteria_queryset(actor: User):
    return QualityCriterion.objects.filter(tenant_id=actor.tenant_id)


def reports_queryset(actor: User):
    from ai.models import AnalyticsReport

    scoped_ids = [ws.id for ws in get_scoped_workspaces(actor)]
    return AnalyticsReport.objects.filter(
        tenant_id=actor.tenant_id,
        workspace_id__in=scoped_ids,
    )


def resolve_report_scope(actor: User, *, workspace_id: str, employee_id: str | None = None):
    from accounts.models import Workspace

    try:
        workspace = Workspace.objects.get(id=workspace_id, tenant_id=actor.tenant_id, is_active=True)
    except Workspace.DoesNotExist:
        return None, None, "Workspace not found."

    scoped_ids = {ws.id for ws in get_scoped_workspaces(actor)}
    if workspace.id not in scoped_ids:
        return None, None, "Workspace outside your scope."

    employee = None
    if employee_id:
        try:
            employee = User.objects.get(id=employee_id, tenant_id=actor.tenant_id, is_active=True)
        except User.DoesNotExist:
            return None, None, "Employee not found."
        if employee.role != User.Role.EMPLOYEE or not user_in_scope(actor, employee):
            return None, None, "Employee outside your scope."
        if employee.workspace_id != workspace.id:
            return None, None, "Employee does not belong to this workspace."

    return workspace, employee, None
