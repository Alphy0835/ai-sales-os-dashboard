from django.core.management.base import BaseCommand

from accounts.models import ModulePermission, Tenant, User, Workspace

MANAGER_PERMISSIONS = {
    ModulePermission.Module.DASHBOARD: ModulePermission.Level.VIEW,
    ModulePermission.Module.CLIENTS: ModulePermission.Level.VIEW,
    ModulePermission.Module.REVIEWS: ModulePermission.Level.EDIT,
    ModulePermission.Module.ANALYTICS: ModulePermission.Level.RUN,
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


class Command(BaseCommand):
    help = "Seed demo tenant, workspace, manager and employee users"

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(
            slug="demo",
            defaults={"name": "Demo Company"},
        )
        workspace, _ = Workspace.objects.get_or_create(
            tenant=tenant,
            name="ОП Москва",
            defaults={"is_active": True},
        )

        manager, created = User.objects.get_or_create(
            tenant=tenant,
            email="manager@demo.local",
            defaults={
                "full_name": "Demo Manager",
                "role": User.Role.MANAGER,
                "workspace": workspace,
                "is_active": True,
            },
        )
        if created:
            manager.set_password("demo1234")
            manager.save()
        set_permissions(manager, MANAGER_PERMISSIONS)

        employee, created = User.objects.get_or_create(
            tenant=tenant,
            email="employee@demo.local",
            defaults={
                "full_name": "Demo Employee",
                "role": User.Role.EMPLOYEE,
                "workspace": workspace,
                "is_active": True,
            },
        )
        if created:
            employee.set_password("demo1234")
            employee.save()
        set_permissions(employee, EMPLOYEE_PERMISSIONS)

        self.stdout.write(self.style.SUCCESS("Demo data ready:"))
        self.stdout.write("  manager@demo.local / demo1234")
        self.stdout.write("  employee@demo.local / demo1234")
