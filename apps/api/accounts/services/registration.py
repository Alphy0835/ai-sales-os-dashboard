from accounts.models import RegistrationInvite, User
from accounts.services.default_permissions import (
    EMPLOYEE_PERMISSIONS,
    MANAGER_PERMISSIONS,
    set_manager_scope,
    set_permissions,
)


def apply_role_defaults(user: User, invite: RegistrationInvite) -> None:
    if invite.role == User.Role.MANAGER:
        set_permissions(user, MANAGER_PERMISSIONS)
        if invite.workspace_id:
            set_manager_scope(user, [invite.workspace])
    else:
        set_permissions(user, EMPLOYEE_PERMISSIONS)
