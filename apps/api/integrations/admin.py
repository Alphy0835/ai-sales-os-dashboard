import json

from django import forms
from django.contrib import admin

from ai.services.crypto import decrypt_secret, encrypt_secret
from integrations.models import (
    ConversationRecording,
    CrmLead,
    IntegrationSource,
    MetricSnapshot,
    Transcription,
)


class IntegrationSourceAdminForm(forms.ModelForm):
    credentials_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=(
            'JSON credentials (encrypted on save). amoCRM: {"access_token": "...", "subdomain": "..."}. '
            "Google Sheets: service account JSON with client_email and private_key."
        ),
    )

    class Meta:
        model = IntegrationSource
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.credentials_encrypted:
            decrypted = decrypt_secret(self.instance.credentials_encrypted)
            if decrypted:
                try:
                    parsed = json.loads(decrypted)
                    self.fields["credentials_json"].initial = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    self.fields["credentials_json"].initial = decrypted

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data.get("credentials_json", "").strip()
        if raw:
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError(f"Invalid credentials JSON: {exc}") from exc
            instance.credentials_encrypted = encrypt_secret(raw)
        instance.save()
        return instance


@admin.register(IntegrationSource)
class IntegrationSourceAdmin(admin.ModelAdmin):
    form = IntegrationSourceAdminForm
    list_display = (
        "name",
        "source_type",
        "tenant",
        "workspace",
        "external_id",
        "status",
        "last_sync_at",
    )
    list_filter = ("source_type", "status", "tenant")
    readonly_fields = ("last_sync_at", "last_error", "created_at")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "config_json" in form.base_fields:
            form.base_fields["config_json"].help_text = (
                'JSON config. Set "provider": "google_sheets" | "amocrm" | "demo". '
                "Google Sheets: spreadsheet_id, sheet_name (default Leads), header_map, skip_status_stages."
            )
        return form


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
    list_filter = ("status",)


@admin.register(CrmLead)
class CrmLeadAdmin(admin.ModelAdmin):
    list_display = (
        "client_name",
        "external_lead_id",
        "employee",
        "pipeline_stage",
        "status_stage",
        "integration_source",
        "synced_at",
    )
    list_filter = ("integration_source", "tenant")
    search_fields = ("client_name", "external_lead_id", "manager_email")
