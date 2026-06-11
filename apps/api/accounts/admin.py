import secrets

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from accounts.models import (
    AuditLog,
    ManagerScope,
    ModulePermission,
    RegistrationInvite,
    Tenant,
    User,
    Workspace,
)
from ai.admin import TenantAiConfigInline, WorkspaceAiConfigInline


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "workspace_count", "created_at")
    search_fields = ("name", "slug")
    inlines = [TenantAiConfigInline]

    @admin.display(description="Workspaces")
    def workspace_count(self, obj):
        count = obj.workspaces.count()
        url = reverse("admin:accounts_workspace_changelist") + f"?tenant__id__exact={obj.pk}"
        return format_html('<a href="{}">{}</a>', url, count)


class RegistrationInviteInline(admin.TabularInline):
    model = RegistrationInvite
    fk_name = "workspace"
    extra = 1
    fields = (
        "code",
        "role",
        "expected_email",
        "expires_at",
        "max_uses",
        "use_count",
        "registration_url_display",
    )
    readonly_fields = ("use_count", "registration_url_display")
    verbose_name_plural = "Регистрация"

    @admin.display(description="Ссылка для регистрации")
    def registration_url_display(self, obj):
        if obj.pk and obj.code:
            return obj.registration_url
        return "— (сохраните invite для генерации ссылки)"


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active")
    list_filter = ("tenant",)
    readonly_fields = ("integrator_help", "crm_sources_link")
    inlines = [WorkspaceAiConfigInline, RegistrationInviteInline]
    fieldsets = (
        (
            "Integrator",
            {
                "fields": ("integrator_help", "crm_sources_link"),
                "description": (
                    "Integrator: создайте invite → настройте AI tier → "
                    "настройте CRM в Integration sources (фильтр по workspace)"
                ),
            },
        ),
        ("Основное", {"fields": ("name", "tenant", "is_active")}),
    )

    @admin.display(description="")
    def integrator_help(self, obj):
        return format_html(
            '<p style="margin:0;">'
            "<strong>Шаги:</strong> 1) Создайте invite ниже → "
            "2) Настройте AI tier → "
            "3) Откройте CRM sources по ссылке справа"
            "</p>"
        )

    @admin.display(description="CRM sources")
    def crm_sources_link(self, obj):
        if not obj.pk:
            return "Сохраните workspace, чтобы настроить CRM"
        url = (
            reverse("admin:integrations_integrationsource_changelist")
            + f"?workspace__id__exact={obj.pk}"
        )
        return format_html(
            '<a href="{}" target="_blank">Открыть Integration sources для этого workspace</a>',
            url,
        )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, "tenant_id") and not instance.tenant_id:
                instance.tenant = form.instance.tenant
            instance.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()


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
        "expected_email",
        "expires_at",
        "use_count",
        "max_uses",
        "used_at",
        "created_at",
    )
    list_filter = ("role", "tenant")
    search_fields = ("code", "expected_email")
    readonly_fields = ("use_count", "used_at", "created_at", "registration_url")
    actions = ["generate_random_codes"]

    @admin.display(description="Ссылка для регистрации")
    def registration_url(self, obj):
        return obj.registration_url

    @admin.action(description="Generate random invite codes")
    def generate_random_codes(self, request, queryset):
        for invite in queryset:
            invite.code = secrets.token_urlsafe(16)
            invite.save(update_fields=["code"])
        self.message_user(request, f"Generated codes for {queryset.count()} invite(s).")
