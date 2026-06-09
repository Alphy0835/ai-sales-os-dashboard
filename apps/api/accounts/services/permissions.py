from accounts.models import ModulePermission

MODULE_ALLOWED_LEVELS: dict[str, tuple[str, ...]] = {
    ModulePermission.Module.DASHBOARD: (
        ModulePermission.Level.NONE,
        ModulePermission.Level.VIEW,
    ),
    ModulePermission.Module.CLIENTS: (
        ModulePermission.Level.NONE,
        ModulePermission.Level.VIEW,
    ),
    ModulePermission.Module.REVIEWS: (
        ModulePermission.Level.NONE,
        ModulePermission.Level.VIEW,
        ModulePermission.Level.EDIT,
    ),
    ModulePermission.Module.ANALYTICS: (
        ModulePermission.Level.NONE,
        ModulePermission.Level.VIEW,
        ModulePermission.Level.RUN,
    ),
    ModulePermission.Module.SETTINGS: (
        ModulePermission.Level.NONE,
        ModulePermission.Level.VIEW,
        ModulePermission.Level.EDIT,
    ),
    ModulePermission.Module.AGENT: (
        ModulePermission.Level.NONE,
        ModulePermission.Level.USE,
    ),
}

MODULE_LEVEL_RANK: dict[str, dict[str, int]] = {
    module: {level: index for index, level in enumerate(levels)}
    for module, levels in MODULE_ALLOWED_LEVELS.items()
}


def get_user_permissions(user) -> dict[str, str]:
    perms = {m.module: m.level for m in user.module_permissions.all()}
    for module in ModulePermission.Module.values:
        perms.setdefault(module, ModulePermission.Level.NONE)
    return perms


def validate_module_level(module: str, level: str) -> str | None:
    allowed = MODULE_ALLOWED_LEVELS.get(module)
    if allowed is None:
        return f"Unknown module: {module}"
    if level not in allowed:
        return f"Invalid level '{level}' for module '{module}'"
    return None


def level_rank(module: str, level: str) -> int:
    return MODULE_LEVEL_RANK[module][level]


def ceiling_allows(grantor_level: str, requested_level: str, module: str) -> bool:
    return level_rank(module, requested_level) <= level_rank(module, grantor_level)


def can_grant_permissions(user) -> bool:
    perms = get_user_permissions(user)
    return perms.get(ModulePermission.Module.SETTINGS) == ModulePermission.Level.EDIT


def can_view_audit(user) -> bool:
    perms = get_user_permissions(user)
    level = perms.get(ModulePermission.Module.SETTINGS, ModulePermission.Level.NONE)
    return level in (ModulePermission.Level.VIEW, ModulePermission.Level.EDIT)
