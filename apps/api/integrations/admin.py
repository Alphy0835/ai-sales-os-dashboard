from django.contrib import admin

from integrations.models import ConversationRecording, IntegrationSource, MetricSnapshot, Transcription


@admin.register(IntegrationSource)
class IntegrationSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "tenant", "workspace", "status", "last_sync_at")
    list_filter = ("source_type", "status", "tenant")


@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ("metric_key", "user", "value", "period_date", "source")
    list_filter = ("metric_key", "period_date")


@admin.register(ConversationRecording)
class ConversationRecordingAdmin(admin.ModelAdmin):
    list_display = ("client_name", "employee", "source_kind", "status", "created_at")
    list_filter = ("source_kind", "status")


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ("recording", "status", "completed_at")
