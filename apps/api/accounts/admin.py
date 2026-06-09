import secrets

from django.contrib import admin

from accounts.models import (
    AuditLog,
    ManagerScope,
    ModulePermission,
    RegistrationInvite,
    Tenant,
    User,
    Workspace,
)


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
        ("Profile", {"fields": ("full_name", "role", "tenant", "workspace", "manager", "external_id")}),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_user", "module", "old_level", "new_level", "created_at")
    list_filter = ("action", "tenant")
    search_fields = ("actor__email", "target_user__email")


@admin.register(RegistrationInvite)
class RegistrationInviteAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "tenant",
        "workspace",
        "role",
        "expires_at",
        "use_count",
        "max_uses",
        "used_at",
        "created_at",
    )
    list_filter = ("role", "tenant")
    search_fields = ("code",)
    readonly_fields = ("use_count", "used_at", "created_at")
    actions = ["generate_random_codes"]

    @admin.action(description="Generate random invite codes")
    def generate_random_codes(self, request, queryset):
        for invite in queryset:
            invite.code = secrets.token_urlsafe(16)
            invite.save(update_fields=["code"])
        self.message_user(request, f"Generated codes for {queryset.count()} invite(s).")
