from accounts.models import ManagerScope, ModulePermission

MANAGER_PERMISSIONS = {
    ModulePermission.Module.DASHBOARD: ModulePermission.Level.VIEW,
    ModulePermission.Module.CLIENTS: ModulePermission.Level.VIEW,
    ModulePermission.Module.REVIEWS: ModulePermission.Level.EDIT,
    ModulePermission.Module.ANALYTICS: ModulePermission.Level.RUN,
    ModulePermission.Module.SETTINGS: ModulePermission.Level.EDIT,
    ModulePermission.Module.AGENT: ModulePermission.Level.USE,
}

REGIONAL_MANAGER_PERMISSIONS = {
    ModulePermission.Module.DASHBOARD: ModulePermission.Level.VIEW,
    ModulePermission.Module.CLIENTS: ModulePermission.Level.VIEW,
    ModulePermission.Module.REVIEWS: ModulePermission.Level.VIEW,
    ModulePermission.Module.ANALYTICS: ModulePermission.Level.VIEW,
    ModulePermission.Module.SETTINGS: ModulePermission.Level.EDIT,
    ModulePermission.Module.AGENT: ModulePermission.Level.USE,
}

EMPLOYEE_PERMISSIONS = {
    ModulePermission.Module.DASHBOARD: ModulePermission.Level.VIEW,
    ModulePermission.Module.CLIENTS: ModulePermission.Level.NONE,
    ModulePermission.Module.REVIEWS: ModulePermission.Level.NONE,
    ModulePermission.Module.ANALYTICS: ModulePermission.Level.NONE,
    ModulePermission.Module.SETTINGS: ModulePermission.Level.NONE,
    ModulePermission.Module.AGENT: ModulePermission.Level.USE,
}


def set_permissions(user, mapping):
    for module, level in mapping.items():
        ModulePermission.objects.update_or_create(
            user=user,
            module=module,
            defaults={"level": level},
        )


def set_manager_scope(user, workspaces):
    for workspace in workspaces:
        ManagerScope.objects.update_or_create(user=user, workspace=workspace)
