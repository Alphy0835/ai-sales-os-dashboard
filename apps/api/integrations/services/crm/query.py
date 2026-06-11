from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django.db.models import Q
from django.utils import timezone

from accounts.models import User, Workspace
from accounts.services.scope import get_accessible_users, get_scoped_workspace_ids
from analytics.models import ClientToReview
from integrations.models import CrmLead, IntegrationSource


@dataclass
class CrmQueryFilters:
    manager_email: str | None = None
    manager_user_id: str | None = None
    pipeline_stage: str | None = None
    status_stage: str | None = None
    search: str | None = None
    needs_review: bool | None = None


def resolve_vocabulary(source: IntegrationSource, field: str, user_term: str) -> str:
    """Map a natural-language term to a canonical CRM value via config_json.crm_vocabulary."""
    if not user_term:
        return user_term
    vocab = (source.config_json or {}).get("crm_vocabulary", {})
    section = vocab.get(field, {})
    term_lower = user_term.strip().lower()
    for canonical, aliases in section.items():
        alias_set = {str(a).strip().lower() for a in aliases if str(a).strip()}
        alias_set.add(str(canonical).strip().lower())
        if term_lower in alias_set:
            return str(canonical)
    return user_term


def _vocabulary_search_terms(source: IntegrationSource, field: str, user_term: str) -> list[str]:
    canonical = resolve_vocabulary(source, field, user_term)
    terms = {user_term.strip(), canonical.strip()} if user_term else set()
    section = (source.config_json or {}).get("crm_vocabulary", {}).get(field, {})
    aliases = section.get(canonical, [])
    terms.update(str(a).strip() for a in aliases if str(a).strip())
    if canonical:
        terms.add(canonical.strip())
    return [t for t in terms if t]


def resolve_tenant_crm_source(actor: User) -> IntegrationSource | None:
    """Pick CRM source for agent queries: scoped to manager OPs, prefer live Google Sheets."""
    qs = IntegrationSource.objects.filter(
        tenant_id=actor.tenant_id,
        is_enabled=True,
        source_type=IntegrationSource.SourceType.CRM,
    )
    scoped_ws = get_scoped_workspace_ids(actor)
    if scoped_ws:
        qs = qs.filter(Q(workspace_id__in=scoped_ws) | Q(workspace__isnull=True))

    gs = (
        qs.filter(config_json__provider="google_sheets")
        .exclude(credentials_encrypted="")
        .order_by("-last_sync_at")
        .first()
    )
    if gs:
        return gs
    return qs.order_by("-last_sync_at").first()


def _resolve_source(
    actor: User,
    integration_source: IntegrationSource | None,
) -> IntegrationSource | None:
    if integration_source is not None:
        if integration_source.tenant_id != actor.tenant_id:
            return None
        return integration_source
    return resolve_tenant_crm_source(actor)


def _lead_to_dict(lead: CrmLead) -> dict:
    return {
        "id": str(lead.id),
        "external_lead_id": lead.external_lead_id,
        "client_name": lead.client_name,
        "phone": lead.phone,
        "city": lead.city,
        "communication_comment": lead.communication_comment,
        "pipeline_stage": lead.pipeline_stage,
        "status_stage": lead.status_stage,
        "manager_email": lead.manager_email,
        "employee_id": str(lead.employee_id) if lead.employee_id else None,
    }


def _apply_actor_scope(qs, actor: User):
    if actor.role == User.Role.EMPLOYEE:
        return qs.filter(
            Q(employee_id=actor.id)
            | Q(employee__isnull=True, manager_email__iexact=actor.email)
        )

    scoped_ws = get_scoped_workspace_ids(actor)
    if not scoped_ws:
        return qs.none()

    employee_ids = [u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE]
    return qs.filter(
        Q(workspace_id__in=scoped_ws)
        | Q(employee_id__in=employee_ids)
        | Q(employee__workspace_id__in=scoped_ws)
    )


def query_crm_leads(
    actor: User,
    *,
    filters: CrmQueryFilters,
    mode: Literal["list", "count"] = "list",
    limit: int = 20,
    integration_source: IntegrationSource | None = None,
) -> dict:
    source = _resolve_source(actor, integration_source)
    if source is not None and (source.config_json or {}).get("provider") == "google_sheets":
        from integrations.services.crm.google_sheets_live import query_google_sheets_live

        return query_google_sheets_live(
            actor,
            source,
            filters=filters,
            mode=mode,
            limit=limit,
        )

    qs = CrmLead.objects.filter(tenant_id=actor.tenant_id).select_related("employee")

    if source is not None:
        qs = qs.filter(integration_source=source)

    qs = _apply_actor_scope(qs, actor)

    if filters.manager_user_id:
        qs = qs.filter(employee_id=filters.manager_user_id)
    elif filters.manager_email:
        qs = qs.filter(
            Q(manager_email__iexact=filters.manager_email)
            | Q(employee__email__iexact=filters.manager_email)
        )

    if filters.pipeline_stage:
        if source is not None:
            terms = _vocabulary_search_terms(source, "stages", filters.pipeline_stage)
            stage_q = Q()
            for term in terms:
                stage_q |= Q(pipeline_stage__icontains=term)
            qs = qs.filter(stage_q)
        else:
            qs = qs.filter(pipeline_stage__icontains=filters.pipeline_stage)

    if filters.status_stage:
        if source is not None:
            terms = _vocabulary_search_terms(source, "statuses", filters.status_stage)
            status_q = Q()
            for term in terms:
                status_q |= Q(status_stage__icontains=term)
            qs = qs.filter(status_q)
        else:
            qs = qs.filter(status_stage__icontains=filters.status_stage)

    if filters.search:
        qs = qs.filter(
            Q(client_name__icontains=filters.search)
            | Q(external_lead_id__icontains=filters.search)
            | Q(phone__icontains=filters.search)
            | Q(communication_comment__icontains=filters.search)
        )

    if filters.needs_review is True:
        review_employee_ids = [
            u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE
        ]
        review_ids = ClientToReview.objects.filter(
            tenant_id=actor.tenant_id,
            employee_id__in=review_employee_ids,
        ).values_list("client_external_id", flat=True)
        qs = qs.filter(external_lead_id__in=review_ids)
    elif filters.needs_review is False:
        review_employee_ids = [
            u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE
        ]
        review_ids = ClientToReview.objects.filter(
            tenant_id=actor.tenant_id,
            employee_id__in=review_employee_ids,
        ).values_list("client_external_id", flat=True)
        qs = qs.exclude(external_lead_id__in=review_ids)

    count = qs.count()
    as_of = source.last_sync_at if source and source.last_sync_at else None

    if mode == "count":
        return {"count": count, "leads": [], "as_of": as_of}

    leads = [_lead_to_dict(lead) for lead in qs[:limit]]
    return {"count": count, "leads": leads, "as_of": as_of}
