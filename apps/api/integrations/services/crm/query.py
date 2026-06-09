from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from accounts.services.scope import get_accessible_users
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


def _resolve_source(
    actor: User,
    integration_source: IntegrationSource | None,
) -> IntegrationSource | None:
    if integration_source is not None:
        if integration_source.tenant_id != actor.tenant_id:
            return None
        return integration_source
    return (
        IntegrationSource.objects.filter(
            tenant_id=actor.tenant_id,
            is_enabled=True,
            source_type=IntegrationSource.SourceType.CRM,
        )
        .order_by("-last_sync_at")
        .first()
    )


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


def _scoped_employee_ids(actor: User) -> list:
    accessible = get_accessible_users(actor)
    return [u.id for u in accessible if u.role == User.Role.EMPLOYEE]


def query_crm_leads(
    actor: User,
    *,
    filters: CrmQueryFilters,
    mode: Literal["list", "count"] = "list",
    limit: int = 20,
    integration_source: IntegrationSource | None = None,
) -> dict:
    source = _resolve_source(actor, integration_source)
    qs = CrmLead.objects.filter(tenant_id=actor.tenant_id).select_related("employee")

    if source is not None:
        qs = qs.filter(integration_source=source)

    employee_ids = _scoped_employee_ids(actor)
    qs = qs.filter(Q(employee_id__in=employee_ids) | Q(employee__isnull=True, manager_email__iexact=actor.email))

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
            | Q(communication_comment__icontains=filters.search)
        )

    if filters.needs_review is True:
        review_ids = ClientToReview.objects.filter(
            tenant_id=actor.tenant_id,
            employee_id__in=employee_ids,
        ).values_list("client_external_id", flat=True)
        qs = qs.filter(external_lead_id__in=review_ids)
    elif filters.needs_review is False:
        review_ids = ClientToReview.objects.filter(
            tenant_id=actor.tenant_id,
            employee_id__in=employee_ids,
        ).values_list("client_external_id", flat=True)
        qs = qs.exclude(external_lead_id__in=review_ids)

    count = qs.count()
    as_of = source.last_sync_at if source and source.last_sync_at else None

    if mode == "count":
        return {"count": count, "leads": [], "as_of": as_of}

    leads = [_lead_to_dict(lead) for lead in qs[:limit]]
    return {"count": count, "leads": leads, "as_of": as_of}
