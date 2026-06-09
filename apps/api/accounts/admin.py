from django.contrib import admin

from accounts.models import ModulePermission, Tenant, User, Workspace


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


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "tenant", "workspace", "is_active")
    list_filter = ("role", "tenant")
    search_fields = ("email", "full_name")
    inlines = [ModulePermissionInline]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "tenant", "workspace")}),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
