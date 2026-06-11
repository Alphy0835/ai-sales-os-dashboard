import json

from django import forms
from django.contrib import admin, messages

from ai.services.crypto import decrypt_secret, encrypt_secret
from integrations.config_templates import GOOGLE_SHEETS_CONFIG_TEMPLATE
from integrations.models import (
    ConversationRecording,
    CrmLead,
    IntegrationSource,
    MetricSnapshot,
    Transcription,
)
from integrations.tasks import sync_integration_source

HEADER_MAP_FIELDS = tuple(GOOGLE_SHEETS_CONFIG_TEMPLATE["header_map"].keys())

HEADER_MAP_LABELS = {
    "lead_id": "ID лида — заголовок колонки (если без буквы A/B)",
    "client_name": "Клиент — заголовок колонки",
    "phone": "Телефон — заголовок колонки",
    "city": "Город — заголовок колонки",
    "communication_comment": "Комментарий — заголовок колонки",
    "manager_email": "Email менеджера — заголовок колонки",
    "supervisor_email": "Email супервайзера — заголовок колонки",
    "pipeline_stage": "Этап воронки — заголовок колонки",
    "status_stage": "Статус — заголовок колонки",
    "recording_url": "Ссылка на запись — заголовок колонки",
    "needs_review": "Разбор (needs_review) — заголовок колонки",
}

COLUMN_MAP_LABELS = {
    "lead_id": "ID лида — колонка (A, B, …)",
    "client_name": "Клиент — колонка",
    "phone": "Телефон — колонка",
    "city": "Город — колонка",
    "communication_comment": "Комментарий — колонка",
    "manager_email": "Email менеджера — колонка",
    "supervisor_email": "Email супервайзера — колонка",
    "pipeline_stage": "Этап воронки — колонка",
    "status_stage": "Статус — колонка",
    "recording_url": "Ссылка на запись — колонка",
    "needs_review": "Разбор — колонка",
}

PROVIDER_CHOICES = [
    ("google_sheets", "Google Sheets"),
    ("amocrm", "amoCRM"),
    ("demo", "Demo"),
]


def _header_map_field_name(internal_field: str) -> str:
    return f"header_map_{internal_field}"


def _column_map_field_name(internal_field: str) -> str:
    return f"column_map_{internal_field}"


def _sheet_header_for_field(header_map: dict, internal_field: str, default: str) -> str:
    matches = [sheet_header for sheet_header, field in header_map.items() if field == internal_field]
    if not matches:
        return default
    for sheet_header in matches:
        if sheet_header != internal_field:
            return sheet_header
    return matches[0]


def _build_header_map_from_form(cleaned_data: dict) -> dict[str, str]:
    header_map: dict[str, str] = {}
    for internal_field in HEADER_MAP_FIELDS:
        form_key = _header_map_field_name(internal_field)
        sheet_header = (cleaned_data.get(form_key) or "").strip()
        if not sheet_header:
            sheet_header = internal_field
        header_map[sheet_header] = internal_field
    return header_map


def _build_column_map_from_form(cleaned_data: dict) -> dict[str, str]:
    column_map: dict[str, str] = {}
    for internal_field in HEADER_MAP_FIELDS:
        form_key = _column_map_field_name(internal_field)
        letter = (cleaned_data.get(form_key) or "").strip().upper()
        if letter:
            column_map[internal_field] = letter
    return column_map


def _advanced_config_from_instance(config: dict) -> str:
    advanced = {}
    if config.get("review_rules"):
        advanced["review_rules"] = config["review_rules"]
    if config.get("crm_vocabulary"):
        advanced["crm_vocabulary"] = config["crm_vocabulary"]
    if not advanced:
        return ""
    return json.dumps(advanced, indent=2, ensure_ascii=False)


def _header_map_form_fields() -> dict[str, forms.CharField]:
    return {
        _header_map_field_name(internal_field): forms.CharField(
            required=False,
            label=HEADER_MAP_LABELS.get(internal_field, internal_field),
            help_text="Только если не указана буква колонки. Строка заголовков = header_row.",
        )
        for internal_field in HEADER_MAP_FIELDS
    }


def _column_map_form_fields() -> dict[str, forms.CharField]:
    return {
        _column_map_field_name(internal_field): forms.CharField(
            required=False,
            label=COLUMN_MAP_LABELS.get(internal_field, internal_field),
            help_text="Буква колонки в Google Sheets (A, B, C…). Приоритет над заголовком.",
        )
        for internal_field in HEADER_MAP_FIELDS
    }


def _build_integration_source_admin_form():
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        config = GOOGLE_SHEETS_CONFIG_TEMPLATE.copy()
        if self.instance and self.instance.pk and self.instance.config_json:
            config = {**GOOGLE_SHEETS_CONFIG_TEMPLATE, **self.instance.config_json}
        elif not self.instance.pk:
            self.initial.setdefault("provider", config.get("provider", "google_sheets"))
            self.initial.setdefault("spreadsheet_id", config.get("spreadsheet_id", ""))
            self.initial.setdefault("sheet_name", config.get("sheet_name", "Leads"))
            self.initial.setdefault("data_start_row", config.get("data_start_row", ""))
            self.initial.setdefault("header_row", config.get("header_row", ""))
            self.initial.setdefault("advanced_config_json", _advanced_config_from_instance(config))

        if self.instance and self.instance.pk:
            self.fields["provider"].initial = config.get("provider", "google_sheets")
            self.fields["spreadsheet_id"].initial = config.get("spreadsheet_id", "")
            self.fields["sheet_name"].initial = config.get("sheet_name", "Leads")
            self.fields["data_start_row"].initial = config.get("data_start_row", "")
            self.fields["header_row"].initial = config.get("header_row", "")
            self.fields["advanced_config_json"].initial = _advanced_config_from_instance(config)
            header_map = config.get("header_map") or {}
            column_map = config.get("column_map") or {}
            for internal_field in HEADER_MAP_FIELDS:
                form_key = _header_map_field_name(internal_field)
                self.fields[form_key].initial = _sheet_header_for_field(
                    header_map,
                    internal_field,
                    internal_field,
                )
                column_key = _column_map_field_name(internal_field)
                self.fields[column_key].initial = column_map.get(internal_field, "")

        if self.instance and self.instance.credentials_encrypted:
            decrypted = decrypt_secret(self.instance.credentials_encrypted)
            if decrypted:
                try:
                    parsed = json.loads(decrypted)
                    self.fields["credentials_json"].initial = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    self.fields["credentials_json"].initial = decrypted

    def clean_advanced_config_json(self):
        raw = (self.cleaned_data.get("advanced_config_json") or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid advanced JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("Advanced JSON must be an object.")
        allowed = {"review_rules", "crm_vocabulary"}
        extra = set(parsed.keys()) - allowed
        if extra:
            raise forms.ValidationError(
                f"Advanced JSON may only contain review_rules and crm_vocabulary; got: {sorted(extra)}"
            )
        return parsed

    def clean(self):
        cleaned_data = forms.ModelForm.clean(self)
        column_map = _build_column_map_from_form(cleaned_data)
        if column_map and ("lead_id" not in column_map or "client_name" not in column_map):
            raise forms.ValidationError(
                "При привязке по колонкам укажите буквы для ID лида и Клиент."
            )
        data_start_row = (cleaned_data.get("data_start_row") or "").strip()
        if data_start_row:
            try:
                row_num = int(data_start_row)
            except ValueError as exc:
                raise forms.ValidationError({"data_start_row": "Укажите номер строки числом."}) from exc
            if row_num < 1:
                raise forms.ValidationError({"data_start_row": "Номер строки должен быть >= 1."})
        header_row = (cleaned_data.get("header_row") or "").strip()
        if header_row:
            try:
                row_num = int(header_row)
            except ValueError as exc:
                raise forms.ValidationError({"header_row": "Укажите номер строки числом."}) from exc
            if row_num < 1:
                raise forms.ValidationError({"header_row": "Номер строки должен быть >= 1."})
        return cleaned_data

    def _pick_json_section(self, key: str, advanced: dict, existing: dict, template: dict):
        if key in advanced:
            return advanced[key]
        if key in existing:
            return existing[key]
        return template.get(key, {} if key != "skip_status_stages" else [])

    def _merge_config_json(self) -> dict:
        existing = {}
        if self.instance and self.instance.pk and self.instance.config_json:
            existing = dict(self.instance.config_json)
        template = GOOGLE_SHEETS_CONFIG_TEMPLATE
        advanced = self.cleaned_data.get("advanced_config_json") or {}
        provider = self.cleaned_data["provider"]

        merged = dict(existing)
        merged["provider"] = provider

        if provider == "google_sheets":
            merged["spreadsheet_id"] = (self.cleaned_data.get("spreadsheet_id") or "").strip()
            merged["sheet_name"] = (self.cleaned_data.get("sheet_name") or "Leads").strip() or "Leads"
            merged["header_map"] = _build_header_map_from_form(self.cleaned_data)
            column_map = _build_column_map_from_form(self.cleaned_data)
            if column_map:
                merged["column_map"] = column_map
            elif "column_map" in merged:
                del merged["column_map"]
            data_start_row = (self.cleaned_data.get("data_start_row") or "").strip()
            if data_start_row:
                merged["data_start_row"] = int(data_start_row)
            elif column_map and "data_start_row" not in merged:
                merged["data_start_row"] = 1
            header_row = (self.cleaned_data.get("header_row") or "").strip()
            if header_row:
                merged["header_row"] = int(header_row)
            elif "header_row" in merged and not header_row:
                del merged["header_row"]
            merged["skip_status_stages"] = self._pick_json_section(
                "skip_status_stages", advanced, existing, template
            )
            merged["review_rules"] = self._pick_json_section("review_rules", advanced, existing, template)
            merged["crm_vocabulary"] = self._pick_json_section("crm_vocabulary", advanced, existing, template)
        else:
            merged["review_rules"] = self._pick_json_section("review_rules", advanced, existing, template)
            merged["crm_vocabulary"] = self._pick_json_section("crm_vocabulary", advanced, existing, template)

        return merged

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)
        instance.config_json = self._merge_config_json()

        raw = self.cleaned_data.get("credentials_json", "").strip()
        if raw:
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError(f"Invalid credentials JSON: {exc}") from exc
            instance.credentials_encrypted = encrypt_secret(raw)

        if commit:
            instance.save()
        return instance

    class Meta:
        model = IntegrationSource
        exclude = ("config_json",)

    attrs = {
        "provider": forms.ChoiceField(
            choices=PROVIDER_CHOICES,
            required=True,
            label="CRM-провайдер",
            help_text="Тип внешнего CRM-источника (сохраняется в config_json.provider).",
        ),
        "spreadsheet_id": forms.CharField(
            required=False,
            label="ID Google Таблицы",
            help_text="Идентификатор таблицы из URL Google Sheets.",
        ),
        "sheet_name": forms.CharField(
            required=False,
            label="Имя листа",
            initial="Leads",
            help_text="Название вкладки с лидами (по умолчанию Leads).",
        ),
        "data_start_row": forms.CharField(
            required=False,
            label="Первая строка данных",
            help_text="Номер строки с первой записью лида (1, 2, 3…). Для привязки по колонкам A/B.",
        ),
        "header_row": forms.CharField(
            required=False,
            label="Строка заголовков",
            help_text="Номер строки с названиями колонок, если привязка по заголовкам (по умолчанию 1).",
        ),
        "advanced_config_json": forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={"rows": 8}),
            label="Расширенный JSON",
            help_text=(
                "Только review_rules и crm_vocabulary. "
                "skip_status_stages сохраняется из существующей конфигурации."
            ),
        ),
        "credentials_json": forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={"rows": 4}),
            help_text=(
                'JSON credentials (encrypted on save). amoCRM: {"access_token": "...", "subdomain": "..."}. '
                "Google Sheets: service account JSON with client_email and private_key."
            ),
        ),
        "__init__": __init__,
        "clean": clean,
        "clean_advanced_config_json": clean_advanced_config_json,
        "_pick_json_section": _pick_json_section,
        "_merge_config_json": _merge_config_json,
        "save": save,
        "Meta": Meta,
    }
    attrs.update(_column_map_form_fields())
    attrs.update(_header_map_form_fields())
    return type("IntegrationSourceAdminForm", (forms.ModelForm,), attrs)


IntegrationSourceAdminForm = _build_integration_source_admin_form()


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
    actions = ["sync_crm_now"]

    def get_fieldsets(self, request, obj=None):
        column_fields = [_column_map_field_name(field) for field in HEADER_MAP_FIELDS]
        header_fields = [_header_map_field_name(field) for field in HEADER_MAP_FIELDS]
        return (
            (
                None,
                {
                    "fields": (
                        "tenant",
                        "workspace",
                        "source_type",
                        "name",
                        "status",
                        "is_enabled",
                        "external_id",
                        "credentials_json",
                        "last_sync_at",
                        "last_error",
                        "created_at",
                    )
                },
            ),
            (
                "CRM configuration",
                {
                    "description": (
                        "Рекомендуется: укажите буквы колонок (A, B, C) и номер первой строки с данными. "
                        "Заголовки в таблице могут быть в любой строке — они не нужны при привязке по колонкам."
                    ),
                    "fields": (
                        "provider",
                        "spreadsheet_id",
                        "sheet_name",
                        "data_start_row",
                        *column_fields,
                        "header_row",
                        *header_fields,
                    )
                },
            ),
            (
                "Advanced JSON",
                {
                    "classes": ("collapse",),
                    "fields": ("advanced_config_json",),
                    "description": (
                        "review_rules и crm_vocabulary. "
                        "Полный config_json собирается автоматически при сохранении."
                    ),
                },
            ),
        )

    @admin.action(description="Refresh metrics and review queue")
    def sync_crm_now(self, request, queryset):
        queued = 0
        skipped = 0

        for source in queryset:
            if source.source_type != IntegrationSource.SourceType.CRM:
                skipped += 1
                continue
            provider = (source.config_json or {}).get("provider")
            if provider != "google_sheets":
                skipped += 1
                continue
            try:
                sync_integration_source.delay(str(source.id), force=True)
                queued += 1
            except Exception as exc:
                self.message_user(
                    request,
                    f"{source.name}: failed to queue sync ({exc})",
                    level=messages.ERROR,
                )

        if queued:
            self.message_user(
                request,
                f"Metrics/review sync queued for {queued} source(s).",
                level=messages.SUCCESS,
            )
        if skipped and not queued:
            self.message_user(
                request,
                f"Skipped {skipped} non-Google-Sheets CRM source(s).",
                level=messages.WARNING,
            )


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
