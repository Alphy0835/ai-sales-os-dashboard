from django.contrib import admin

from ai.models import AgentChatMessage, AgentChatSession, AnalyticsReport, CustomReport, KnowledgeArticle, QualityCriterion


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
