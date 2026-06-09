import logging

from django.utils import timezone

from accounts.models import User
from analytics.models import ClientToReview
from integrations.models import CrmLead, IntegrationSource
from integrations.services.crm_adapter import CrmAdapterError, decrypt_source_credentials

logger = logging.getLogger(__name__)

DEFAULT_HEADER_MAP = {
    "lead_id": "lead_id",
    "client_name": "client_name",
    "phone": "phone",
    "city": "city",
    "communication_comment": "communication_comment",
    "manager_email": "manager_email",
    "supervisor_email": "supervisor_email",
    "pipeline_stage": "pipeline_stage",
    "status_stage": "status_stage",
    "recording_url": "recording_url",
    "needs_review": "needs_review",
    "разбор": "needs_review",
}

DEFAULT_SKIP_STATUS_STAGES = ["done", "closed"]


def _header_map(source: IntegrationSource) -> dict[str, str]:
    config = source.config_json or {}
    custom = config.get("header_map") or {}
    return {**DEFAULT_HEADER_MAP, **custom}


def _skip_status_stages(source: IntegrationSource) -> set[str]:
    config = source.config_json or {}
    stages = config.get("skip_status_stages", DEFAULT_SKIP_STATUS_STAGES)
    return {str(s).strip().lower() for s in stages if str(s).strip()}


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in ("true", "да", "1", "yes")


def _should_add_to_review(source: IntegrationSource, row: dict[str, str]) -> tuple[bool, str]:
    config = source.config_json or {}
    review_rules = config.get("review_rules", {})

    needs_review_val = row.get("needs_review", "").strip()
    if needs_review_val and _parse_bool(needs_review_val):
        reason = row.get("communication_comment") or "Flagged for review"
        return True, reason

    auto_statuses = config.get("auto_review_statuses") or review_rules.get("auto_review_statuses") or []
    status_stage = row.get("status_stage", "").strip().lower()
    if auto_statuses:
        auto_set = {str(s).strip().lower() for s in auto_statuses if str(s).strip()}
        if status_stage in auto_set:
            return True, row.get("communication_comment") or status_stage

    skip_stages = _skip_status_stages(source)
    if status_stage in skip_stages:
        return False, ""

    empty_comment_on_active = review_rules.get("empty_comment_on_active", True)
    if empty_comment_on_active and not row.get("communication_comment", "").strip():
        return True, row.get("pipeline_stage") or "Empty comment"

    return False, ""


def _read_sheet_rows(source: IntegrationSource, credentials: dict) -> list[dict[str, str]]:
    spreadsheet_id = (source.config_json or {}).get("spreadsheet_id", "")
    if not spreadsheet_id:
        raise CrmAdapterError("spreadsheet_id missing in config_json")

    sheet_name = (source.config_json or {}).get("sheet_name", "Leads")
    header_map = _header_map(source)
    reverse_map = {v.strip().lower(): k for k, v in header_map.items()}

    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_info(
        credentials,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:Z")
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []

    headers = [str(h).strip().lower() for h in values[0]]
    col_index = {}
    for idx, header in enumerate(headers):
        field = reverse_map.get(header)
        if field:
            col_index[field] = idx

    if "lead_id" not in col_index or "client_name" not in col_index:
        raise CrmAdapterError("Sheet must include lead_id and client_name columns")

    rows: list[dict[str, str]] = []
    for raw_row in values[1:]:
        row: dict[str, str] = {}
        for field, idx in col_index.items():
            if idx < len(raw_row):
                row[field] = str(raw_row[idx]).strip()
            else:
                row[field] = ""
        if row.get("lead_id") and row.get("client_name"):
            rows.append(row)
    return rows


def _resolve_employee(source: IntegrationSource, manager_email: str) -> User | None:
    email = manager_email.strip().lower()
    if not email:
        return None
    return (
        User.objects.filter(
            tenant_id=source.tenant_id,
            email__iexact=email,
            role__in=[User.Role.EMPLOYEE, User.Role.MANAGER],
            is_active=True,
        )
        .order_by("role")
        .first()
    )


def _upsert_client_to_review(
    source: IntegrationSource,
    *,
    employee: User,
    lead_id: str,
    client_name: str,
    reason: str,
) -> None:
    workspace = employee.workspace or source.workspace
    if not workspace:
        return

    ClientToReview.objects.update_or_create(
        tenant_id=source.tenant_id,
        workspace=workspace,
        employee=employee,
        client_external_id=lead_id,
        defaults={
            "client_name": client_name,
            "reason": reason or "CRM lead",
            "status": ClientToReview.Status.NEW,
        },
    )


def sync_google_sheets(source: IntegrationSource) -> None:
    credentials = decrypt_source_credentials(source)
    if not credentials.get("client_email") or not credentials.get("private_key"):
        source.status = IntegrationSource.Status.ERROR
        source.last_error = "Missing Google service account credentials"
        source.last_sync_at = timezone.now()
        source.save(update_fields=["status", "last_error", "last_sync_at"])
        return

    skip_stages = _skip_status_stages(source)

    try:
        rows = _read_sheet_rows(source, credentials)
        for row in rows:
            employee = _resolve_employee(source, row.get("manager_email", ""))
            defaults = {
                "client_name": row["client_name"],
                "phone": row.get("phone", ""),
                "city": row.get("city", ""),
                "communication_comment": row.get("communication_comment", ""),
                "pipeline_stage": row.get("pipeline_stage", ""),
                "status_stage": row.get("status_stage", ""),
                "recording_url": row.get("recording_url", ""),
                "manager_email": row.get("manager_email", ""),
                "supervisor_email": row.get("supervisor_email", ""),
                "workspace": source.workspace,
                "employee": employee,
            }
            CrmLead.objects.update_or_create(
                tenant_id=source.tenant_id,
                external_lead_id=row["lead_id"],
                integration_source=source,
                defaults=defaults,
            )

            if employee:
                add_review, reason = _should_add_to_review(source, row)
                if add_review:
                    _upsert_client_to_review(
                        source,
                        employee=employee,
                        lead_id=row["lead_id"],
                        client_name=row["client_name"],
                        reason=reason,
                    )

        source.status = IntegrationSource.Status.CONNECTED
        source.last_error = ""
        source.last_sync_at = timezone.now()
        source.save(update_fields=["status", "last_error", "last_sync_at"])
    except CrmAdapterError as exc:
        logger.warning("Google Sheets sync failed for source %s: %s", source.id, exc)
        source.status = IntegrationSource.Status.ERROR
        source.last_error = str(exc)[:500]
        source.last_sync_at = timezone.now()
        source.save(update_fields=["status", "last_error", "last_sync_at"])
    except Exception as exc:
        logger.warning("Google Sheets sync failed for source %s: %s", source.id, exc)
        source.status = IntegrationSource.Status.ERROR
        source.last_error = str(exc)[:500]
        source.last_sync_at = timezone.now()
        source.save(update_fields=["status", "last_error", "last_sync_at"])
