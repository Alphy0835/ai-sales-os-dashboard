from django.core.management.base import BaseCommand

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace

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


class Command(BaseCommand):
    help = "Seed demo tenant, workspaces, hierarchy, manager and employee users"

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(
            slug="demo",
            defaults={"name": "Demo Company"},
        )
        moscow, _ = Workspace.objects.get_or_create(
            tenant=tenant,
            name="ОП Москва",
            defaults={"is_active": True},
        )
        spb, _ = Workspace.objects.get_or_create(
            tenant=tenant,
            name="ОП СПб",
            defaults={"is_active": True},
        )

        top_manager, created = User.objects.get_or_create(
            tenant=tenant,
            email="manager@demo.local",
            defaults={
                "full_name": "Demo Manager",
                "role": User.Role.MANAGER,
                "workspace": moscow,
                "is_active": True,
            },
        )
        if created:
            top_manager.set_password("demo1234")
            top_manager.save()
        set_permissions(top_manager, MANAGER_PERMISSIONS)
        set_manager_scope(top_manager, [moscow, spb])

        regional_manager, created = User.objects.get_or_create(
            tenant=tenant,
            email="regional@demo.local",
            defaults={
                "full_name": "Regional Manager",
                "role": User.Role.MANAGER,
                "workspace": moscow,
                "manager": top_manager,
                "is_active": True,
            },
        )
        if created:
            regional_manager.set_password("demo1234")
            regional_manager.save()
        else:
            regional_manager.manager = top_manager
            regional_manager.save(update_fields=["manager"])
        set_permissions(regional_manager, REGIONAL_MANAGER_PERMISSIONS)
        set_manager_scope(regional_manager, [moscow])

        employee, created = User.objects.get_or_create(
            tenant=tenant,
            email="employee@demo.local",
            defaults={
                "full_name": "Demo Employee",
                "role": User.Role.EMPLOYEE,
                "workspace": moscow,
                "is_active": True,
            },
        )
        if created:
            employee.set_password("demo1234")
            employee.save()
        set_permissions(employee, EMPLOYEE_PERMISSIONS)

        spb_employee, created = User.objects.get_or_create(
            tenant=tenant,
            email="employee-spb@demo.local",
            defaults={
                "full_name": "SPB Employee",
                "role": User.Role.EMPLOYEE,
                "workspace": spb,
                "is_active": True,
            },
        )
        if created:
            spb_employee.set_password("demo1234")
            spb_employee.save()
        set_permissions(spb_employee, EMPLOYEE_PERMISSIONS)

        from django.core.management import call_command

        call_command("seed_integrations")
        call_command("seed_dashboard")
        call_command("seed_reviews")
        call_command("seed_ai")
        call_command("seed_knowledge")
        call_command("seed_custom_reports")

        self.stdout.write(self.style.SUCCESS("Demo data ready:"))
        self.stdout.write("  manager@demo.local / demo1234 (top manager, both workspaces)")
        self.stdout.write("  regional@demo.local / demo1234 (sub-manager, ОП Москва only)")
        self.stdout.write("  employee@demo.local / demo1234 (ОП Москва)")
        self.stdout.write("  employee-spb@demo.local / demo1234 (ОП СПб, outside regional scope)")
