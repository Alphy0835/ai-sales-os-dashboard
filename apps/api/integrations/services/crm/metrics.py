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
    """Legacy CrmLead deals count for Google Sheets (pre-hybrid sync).

    Prefer MetricSnapshot.metric_key=deals written by sync_google_sheets_metrics.
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
