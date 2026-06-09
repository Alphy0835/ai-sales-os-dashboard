from django.db import transaction

from accounts.models import ModulePermission
from accounts.services.audit import log_permission_change
from accounts.services.permissions import (
    ceiling_allows,
    get_user_permissions,
    validate_module_level,
)
from accounts.services.scope import user_in_scope


class PermissionGrantError(Exception):
    def __init__(self, message, code="invalid"):
        super().__init__(message)
        self.code = code


@transaction.atomic
def grant_permissions(*, grantor, target_user, permissions: dict[str, str], ip_address=None):
    if not user_in_scope(grantor, target_user):
        raise PermissionGrantError("Target user is outside your scope", code="scope_denied")

    grantor_perms = get_user_permissions(grantor)
    errors: dict[str, list[str]] = {}

    for module, level in permissions.items():
        validation_error = validate_module_level(module, level)
        if validation_error:
            errors.setdefault(module, []).append(validation_error)
            continue
        if not ceiling_allows(grantor_perms.get(module, ModulePermission.Level.NONE), level, module):
            errors.setdefault(module, []).append(
                "Requested level exceeds grantor ceiling (REQ-014)"
            )

    if errors:
        raise PermissionGrantError(errors, code="ceiling_violation")

    for module, level in permissions.items():
        perm, created = ModulePermission.objects.get_or_create(
            user=target_user,
            module=module,
            defaults={"level": level},
        )
        old_level = ModulePermission.Level.NONE if created else perm.level
        if old_level != level:
            perm.level = level
            perm.save(update_fields=["level"])
            log_permission_change(
                actor=grantor,
                target_user=target_user,
                module=module,
                old_level=old_level,
                new_level=level,
                ip_address=ip_address,
            )

    return get_user_permissions(target_user)
