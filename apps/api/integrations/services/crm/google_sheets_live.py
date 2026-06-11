from __future__ import annotations

from typing import Literal

from django.utils import timezone

from accounts.models import User
from accounts.services.scope import get_accessible_users, get_scoped_workspace_ids
from analytics.models import ClientToReview
from integrations.models import IntegrationSource
from integrations.services.crm.google_sheets import _resolve_employee, read_sheet_rows_cached
from integrations.services.crm.query import CrmQueryFilters, _vocabulary_search_terms
from integrations.services.crm_adapter import CrmAdapterError, decrypt_source_credentials


def _row_to_dict(row: dict[str, str], employee: User | None) -> dict:
    return {
        "id": row["lead_id"],
        "external_lead_id": row["lead_id"],
        "client_name": row["client_name"],
        "phone": row.get("phone", ""),
        "city": row.get("city", ""),
        "communication_comment": row.get("communication_comment", ""),
        "pipeline_stage": row.get("pipeline_stage", ""),
        "status_stage": row.get("status_stage", ""),
        "manager_email": row.get("manager_email", ""),
        "employee_id": str(employee.id) if employee else None,
    }


def _row_matches_search(row: dict[str, str], search: str) -> bool:
    needle = search.lower()
    for field in ("client_name", "lead_id", "phone", "communication_comment"):
        if needle in (row.get(field) or "").lower():
            return True
    return False


def _row_matches_vocabulary_field(
    row: dict[str, str],
    source: IntegrationSource,
    vocab_field: str,
    row_field: str,
    user_term: str,
) -> bool:
    terms = _vocabulary_search_terms(source, vocab_field, user_term)
    value = (row.get(row_field) or "").lower()
    return any(term.lower() in value for term in terms)


def _row_in_scope(actor: User, source: IntegrationSource, row: dict[str, str], employee: User | None) -> bool:
    if actor.role == User.Role.EMPLOYEE:
        if employee and employee.id == actor.id:
            return True
        manager_email = (row.get("manager_email") or "").strip().lower()
        return employee is None and manager_email == actor.email.lower()

    scoped_ws = {str(w) for w in get_scoped_workspace_ids(actor)}
    if not scoped_ws:
        return False

    employee_ids = {u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE}
    workspace_id = None
    if employee and employee.workspace_id:
        workspace_id = str(employee.workspace_id)
    elif source.workspace_id:
        workspace_id = str(source.workspace_id)

    if workspace_id and workspace_id in scoped_ws:
        return True
    if employee and employee.id in employee_ids:
        return True
    if employee and employee.workspace_id and str(employee.workspace_id) in scoped_ws:
        return True
    return False


def _review_external_ids(actor: User) -> set[str]:
    review_employee_ids = [
        u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE
    ]
    return set(
        ClientToReview.objects.filter(
            tenant_id=actor.tenant_id,
            employee_id__in=review_employee_ids,
        ).values_list("client_external_id", flat=True)
    )


def _apply_filters(
    actor: User,
    source: IntegrationSource,
    rows: list[tuple[dict[str, str], User | None]],
    filters: CrmQueryFilters,
) -> list[tuple[dict[str, str], User | None]]:
    review_ids: set[str] | None = None
    if filters.needs_review is not None:
        review_ids = _review_external_ids(actor)

    filtered: list[tuple[dict[str, str], User | None]] = []
    for row, employee in rows:
        if filters.manager_user_id:
            if not employee or str(employee.id) != str(filters.manager_user_id):
                continue
        elif filters.manager_email:
            manager_email = (row.get("manager_email") or "").strip().lower()
            employee_email = employee.email.lower() if employee else ""
            target = filters.manager_email.strip().lower()
            if manager_email != target and employee_email != target:
                continue

        if filters.pipeline_stage and not _row_matches_vocabulary_field(
            row, source, "stages", "pipeline_stage", filters.pipeline_stage
        ):
            continue

        if filters.status_stage and not _row_matches_vocabulary_field(
            row, source, "statuses", "status_stage", filters.status_stage
        ):
            continue

        if filters.search and not _row_matches_search(row, filters.search):
            continue

        lead_id = row.get("lead_id", "")
        if filters.needs_review is True and lead_id not in review_ids:
            continue
        if filters.needs_review is False and lead_id in review_ids:
            continue

        filtered.append((row, employee))
    return filtered


def query_google_sheets_live(
    actor: User,
    source: IntegrationSource,
    *,
    filters: CrmQueryFilters,
    mode: Literal["list", "count"] = "list",
    limit: int = 20,
) -> dict:
    credentials = decrypt_source_credentials(source)
    if not credentials.get("client_email") or not credentials.get("private_key"):
        raise CrmAdapterError("Missing Google service account credentials")

    rows = read_sheet_rows_cached(source, credentials)
    scoped_rows: list[tuple[dict[str, str], User | None]] = []
    for row in rows:
        employee = _resolve_employee(source, row.get("manager_email", ""))
        if _row_in_scope(actor, source, row, employee):
            scoped_rows.append((row, employee))

    filtered = _apply_filters(actor, source, scoped_rows, filters)
    as_of = timezone.now()
    count = len(filtered)

    if mode == "count":
        return {"count": count, "leads": [], "as_of": as_of}

    leads = [_row_to_dict(row, employee) for row, employee in filtered[:limit]]
    return {"count": count, "leads": leads, "as_of": as_of}
