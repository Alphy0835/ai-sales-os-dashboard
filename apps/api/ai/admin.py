from django.contrib import admin

from ai.models import AnalyticsReport, QualityCriterion


@admin.register(QualityCriterion)
class QualityCriterionAdmin(admin.ModelAdmin):
    list_display = ("name", "funnel_stage", "tenant", "is_active", "sort_order")
    list_filter = ("funnel_stage", "is_active")


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ("template", "workspace", "employee", "status", "created_at")
    list_filter = ("template", "status")
