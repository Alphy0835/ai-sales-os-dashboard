from accounts.models import AuditLog


def log_permission_change(*, actor, target_user, module, old_level, new_level, ip_address=None):
    return AuditLog.objects.create(
        tenant=actor.tenant,
        actor=actor,
        target_user=target_user,
        action=AuditLog.Action.PERMISSION_CHANGE,
        module=module,
        old_level=old_level,
        new_level=new_level,
        ip_address=ip_address,
    )


def log_scope_denied(*, actor, target_user, ip_address=None):
    return AuditLog.objects.create(
        tenant=actor.tenant,
        actor=actor,
        target_user=target_user,
        action=AuditLog.Action.SCOPE_DENIED,
        ip_address=ip_address,
    )
