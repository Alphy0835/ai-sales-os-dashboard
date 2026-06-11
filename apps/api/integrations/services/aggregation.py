from datetime import date, timedelta
from uuid import UUID

from django.db.models import Q, Sum
from django.utils import timezone

from accounts.models import User
from accounts.services.scope import get_accessible_users, get_scoped_workspace_ids
from integrations.models import IntegrationSource, MetricSnapshot
from integrations.services.health import crm_stale_reason, is_crm_source_stale

METRIC_DEFINITIONS = {
    "calls": {"sources": [IntegrationSource.SourceType.TELEPHONY], "label": "Звонки"},
    "deals": {"sources": [IntegrationSource.SourceType.CRM], "label": "Сделки"},
    "revenue": {
        "sources": [IntegrationSource.SourceType.CRM, IntegrationSource.SourceType.REPORTING],
        "label": "Выручка",
    },
    "meetings": {"sources": [IntegrationSource.SourceType.REPORTING], "label": "Встречи"},
    "quality_score": {"sources": [IntegrationSource.SourceType.TELEPHONY], "label": "Оценка качества"},
}


def period_bounds(period: str, today: date | None = None) -> tuple[date, date]:
    today = today or timezone.localdate()
    if period == "week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if period == "month":
        return today.replace(day=1), today
    return today, today


def accessible_employees(actor: User):
    if actor.role == User.Role.EMPLOYEE:
        return [actor]
    return [u for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE]


def filter_employees(actor: User, user_id: str | None):
    employees = accessible_employees(actor)
    if not user_id:
        return employees
    return [e for e in employees if str(e.id) == str(user_id)]


def tenant_sources(tenant_id, workspace_ids):
    qs = IntegrationSource.objects.filter(tenant_id=tenant_id, is_enabled=True)
    if workspace_ids:
        qs = qs.filter(Q(workspace_id__in=workspace_ids) | Q(workspace__isnull=True))
    return list(qs)


def source_health(sources):
    entries = []
    for s in sources:
        stale = is_crm_source_stale(s) if s.source_type == IntegrationSource.SourceType.CRM else False
        entries.append(
            {
                "id": str(s.id),
                "source_type": s.source_type,
                "name": s.name,
                "status": s.status,
                "last_sync_at": s.last_sync_at,
                "last_error": s.last_error or None,
                "stale": stale,
                "stale_reason": crm_stale_reason(s) if stale else None,
            }
        )
    return entries


def compute_completeness(sources, metrics_payload):
    if not sources:
        return "empty", "Нет подключённых источников"
    statuses = {s.source_type: s.status for s in sources}
    unavailable = [
        t for t, st in statuses.items() if st in (IntegrationSource.Status.DISCONNECTED, IntegrationSource.Status.ERROR)
    ]
    degraded = [t for t, st in statuses.items() if st == IntegrationSource.Status.DEGRADED]
    missing_metrics = [k for k, v in metrics_payload.items() if not v["available"]]

    if unavailable and len(unavailable) == len(statuses):
        return "empty", "Все источники недоступны"
    if unavailable or degraded or missing_metrics:
        parts = []
        if unavailable:
            parts.append(f"недоступны: {', '.join(unavailable)}")
        if degraded:
            parts.append(f"частично: {', '.join(degraded)}")
        return "partial", "; ".join(parts) or "Частичные данные"
    return "full", None


def build_metrics_summary(*, actor: User, period: str = "today", workspace_id: str | None = None, user_id: str | None = None):
    employees = filter_employees(actor, user_id)
    if user_id and not employees:
        return None

    workspace_ids = get_scoped_workspace_ids(actor)
    if workspace_id:
        scoped = {str(w) for w in workspace_ids}
        if str(workspace_id) not in scoped and actor.role != User.Role.EMPLOYEE:
            return None
        workspace_ids = {UUID(str(workspace_id))}

    if actor.role == User.Role.EMPLOYEE and actor.workspace_id:
        workspace_ids = {str(actor.workspace_id)}

    sources = tenant_sources(actor.tenant_id, workspace_ids)
    start, end = period_bounds("today" if period == "today" else period)

    employee_ids = [e.id for e in employees]
    snapshots = MetricSnapshot.objects.filter(
        tenant_id=actor.tenant_id,
        user_id__in=employee_ids,
        period_date__gte=start,
        period_date__lte=end,
    )
    if workspace_ids:
        snapshots = snapshots.filter(workspace_id__in=workspace_ids)

    metrics_payload = {}
    for key, definition in METRIC_DEFINITIONS.items():
        required_types = definition["sources"]
        type_status = {
            t: next((s.status for s in sources if s.source_type == t), IntegrationSource.Status.DISCONNECTED)
            for t in required_types
        }
        telephony_degraded = (
            key == "quality_score"
            and type_status.get(IntegrationSource.SourceType.TELEPHONY)
            == IntegrationSource.Status.DEGRADED
        )
        usable_types = [
            t
            for t in required_types
            if type_status[t] in (IntegrationSource.Status.CONNECTED, IntegrationSource.Status.DEGRADED)
        ]
        available = bool(usable_types) and not telephony_degraded
        reason = None
        if telephony_degraded:
            reason = "telephony_degraded"
        elif not usable_types:
            reason = f"Источник недоступен: {', '.join(required_types)}"

        value = None
        if available:
            agg = snapshots.filter(
                metric_key=key,
                source__source_type__in=usable_types,
            ).aggregate(total=Sum("value"))
            total = agg["total"]
            if total is None:
                if employee_ids:
                    available = False
                    reason = reason or "Нет данных за период"
                else:
                    value = 0.0
            else:
                value = float(total)

        metrics_payload[key] = {
            "label": definition["label"],
            "value": value,
            "available": available,
            "sources": usable_types,
            "reason": reason,
        }

    completeness, completeness_reason = compute_completeness(sources, metrics_payload)

    return {
        "period": period,
        "as_of": timezone.now(),
        "workspace_id": workspace_id,
        "user_id": user_id,
        "completeness": completeness,
        "completeness_reason": completeness_reason,
        "sources": source_health(sources),
        "metrics": metrics_payload,
    }
