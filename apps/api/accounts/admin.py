from django.contrib import admin

from accounts.models import AuditLog, ManagerScope, ModulePermission, Tenant, User, Workspace


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active")
    list_filter = ("tenant",)


class ModulePermissionInline(admin.TabularInline):
    model = ModulePermission
    extra = 0


class ManagerScopeInline(admin.TabularInline):
    model = ManagerScope
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "tenant", "workspace", "manager", "is_active")
    list_filter = ("role", "tenant")
    search_fields = ("email", "full_name")
    inlines = [ModulePermissionInline, ManagerScopeInline]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "tenant", "workspace", "manager")}),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_user", "module", "old_level", "new_level", "created_at")
    list_filter = ("action", "tenant")
    search_fields = ("actor__email", "target_user__email")
