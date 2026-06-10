from datetime import date
from uuid import UUID

from django.db.models import Q

from integrations.models import CrmLead, IntegrationSource


def google_sheets_crm_sources(sources: list[IntegrationSource]) -> list[IntegrationSource]:
    return [
        s
        for s in sources
        if s.source_type == IntegrationSource.SourceType.CRM
        and (s.config_json or {}).get("provider") == "google_sheets"
    ]


def count_crm_leads_deals(
    *,
    tenant_id,
    source_ids,
    workspace_ids,
    employee_ids,
    start: date,
    end: date,
) -> int:
    """Count CrmLead rows as a deals fallback for Google Sheets CRM.

    Google Sheets sync upserts CrmLead but does not write MetricSnapshot.
    We use ``synced_at`` (updated on each sync upsert) as the period proxy
    because the sheet schema has no reliable per-deal close date field.
    """
    if not employee_ids:
        return 0

    qs = CrmLead.objects.filter(
        tenant_id=tenant_id,
        integration_source_id__in=source_ids,
        synced_at__date__gte=start,
        synced_at__date__lte=end,
        employee_id__in=employee_ids,
    )
    if workspace_ids:
        ws_ids = {UUID(str(w)) for w in workspace_ids}
        qs = qs.filter(Q(workspace_id__in=ws_ids) | Q(workspace__isnull=True))
    return qs.count()
