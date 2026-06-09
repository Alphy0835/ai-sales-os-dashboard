import json

from django import forms
from django.contrib import admin

from ai.services.crypto import decrypt_secret, encrypt_secret
from integrations.models import ConversationRecording, IntegrationSource, MetricSnapshot, Transcription


class IntegrationSourceAdminForm(forms.ModelForm):
    credentials_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text='JSON: {"access_token": "...", "subdomain": "..."} (encrypted on save)',
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
