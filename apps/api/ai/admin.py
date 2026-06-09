from django import forms
from django.contrib import admin

from ai.models import (
    AgentChatMessage,
    AgentChatSession,
    AnalyticsReport,
    CustomReport,
    KnowledgeArticle,
    KnowledgeArticleGrant,
    QualityCriterion,
    TenantAiConfig,
    WorkspaceAiConfig,
)
from ai.services.crypto import encrypt_secret


class EncryptedApiKeyMixin:
    api_key_plain = forms.CharField(
        label="API key",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the current key.",
    )

    def save_model(self, request, obj, form, change):
        plain = form.cleaned_data.get("api_key_plain", "")
        if plain:
            obj.api_key_encrypted = encrypt_secret(plain)
        super().save_model(request, obj, form, change)


@admin.register(TenantAiConfig)
class TenantAiConfigAdmin(EncryptedApiKeyMixin, admin.ModelAdmin):
    list_display = ("tenant", "is_enabled", "chat_model", "embedding_model", "updated_at")
    readonly_fields = ("updated_at",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.api_key_encrypted:
            form.base_fields["api_key_plain"].help_text = "Stored (encrypted). Enter a new value to replace."
        return form


@admin.register(WorkspaceAiConfig)
class WorkspaceAiConfigAdmin(EncryptedApiKeyMixin, admin.ModelAdmin):
    list_display = ("workspace", "is_enabled", "chat_model", "embedding_model", "updated_at")
    readonly_fields = ("updated_at",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.api_key_encrypted:
            form.base_fields["api_key_plain"].help_text = "Stored (encrypted). Enter a new value to replace."
        return form


@admin.register(KnowledgeArticleGrant)
class KnowledgeArticleGrantAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "is_allowed", "tenant", "updated_at")
    list_filter = ("is_allowed",)


@admin.register(QualityCriterion)
class QualityCriterionAdmin(admin.ModelAdmin):
    list_display = ("name", "funnel_stage", "tenant", "is_active", "sort_order")
    list_filter = ("funnel_stage", "is_active")


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ("template", "workspace", "employee", "status", "created_at")
    list_filter = ("template", "status")


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "access_level", "tenant", "is_active")
    list_filter = ("category", "access_level")


@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "tenant", "is_active", "updated_at")
    list_filter = ("is_active",)


@admin.register(AgentChatSession)
class AgentChatSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "agent_role", "client_name", "created_at")


@admin.register(AgentChatMessage)
class AgentChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "created_at")
