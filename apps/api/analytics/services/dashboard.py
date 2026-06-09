from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Sum
from django.utils import timezone

from accounts.models import User
from accounts.services.scope import get_accessible_users, get_scoped_workspaces, user_in_scope
from analytics.models import ClientToReview
from integrations.models import MetricSnapshot
from integrations.services.aggregation import build_metrics_summary, period_bounds

PLAN_CALLS_PER_DAY = Decimal("10")
PLAN_QUALITY = Decimal("80")


def _employee_metrics(tenant_id, employee_ids, workspace_ids, start, end):
    qs = MetricSnapshot.objects.filter(
        tenant_id=tenant_id,
        user_id__in=employee_ids,
        period_date__gte=start,
        period_date__lte=end,
    )
    if workspace_ids:
        qs = qs.filter(workspace_id__in=workspace_ids)

    rows = []
    for emp_id in employee_ids:
        emp_qs = qs.filter(user_id=emp_id)
        calls = emp_qs.filter(metric_key="calls").aggregate(t=Sum("value"))["t"] or Decimal("0")
        quality = emp_qs.filter(metric_key="quality_score").aggregate(t=Avg("value"))["t"]
        rows.append(
            {
                "user_id": emp_id,
                "calls": float(calls),
                "quality_score": float(quality) if quality is not None else None,
            }
        )
    return rows


def _status_for_employee(calls: float, quality: float | None) -> str:
    if quality is not None and quality < 70:
        return "risk"
    if calls < float(PLAN_CALLS_PER_DAY) * 0.7 or (quality is not None and quality < 78):
        return "warn"
    return "ok"


def _trend_series(tenant_id, employee_ids, workspace_ids, days=7):
    today = timezone.localdate()
    labels = []
    values = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%d.%m"))
        qs = MetricSnapshot.objects.filter(
            tenant_id=tenant_id,
            user_id__in=employee_ids,
            metric_key="calls",
            period_date=day,
        )
        if workspace_ids:
            qs = qs.filter(workspace_id__in=workspace_ids)
        total = qs.aggregate(t=Sum("value"))["t"] or Decimal("0")
        values.append(float(total))
    return {"labels": labels, "values": values}


def _build_ai_summary(*, metrics_today, employees_table, completeness):
    if completeness == "empty":
        return None

    warn_employees = [e for e in employees_table if e["status"] in ("warn", "risk")]
    if not warn_employees and metrics_today["completeness"] == "full":
        top = max(employees_table, key=lambda e: e.get("quality_score") or 0, default=None)
        if top and top.get("quality_score"):
            return {
                "available": True,
                "confidence": 82,
                "text": f"Показатели в норме. Отметить: {top['full_name']} — стабильное качество общения.",
                "sources": ["crm", "telephony", "reporting"],
                "highlights": [
                    {"type": "praise", "text": f"{top['full_name']} — качество {top['quality_score']:.0f}%"},
                ],
            }

    if not warn_employees:
        return None

    names = ", ".join(e["full_name"] for e in warn_employees[:3])
    text = f"Снижение активности или качества у: {names}. Рекомендуется разбор на основе записей за неделю."
    if metrics_today["completeness"] == "partial":
        text += " Часть метрик качества недоступна (телефония)."

    return {
        "available": True,
        "confidence": 75 if metrics_today["completeness"] == "partial" else 87,
        "text": text,
        "sources": ["telephony", "crm"],
        "highlights": [
            {"type": "control" if e["status"] == "warn" else "risk", "text": f"{e['full_name']} — {e['status_label']}"}
            for e in warn_employees[:3]
        ],
    }


def build_manager_dashboard(*, actor: User, workspace_id: str | None = None, user_id: str | None = None):
    workspaces = list(get_scoped_workspaces(actor))
    workspace_ids = {w.id for w in workspaces}

    if workspace_id:
        if workspace_id not in {str(w.id) for w in workspaces}:
            return None
        from uuid import UUID

        workspace_ids = {UUID(workspace_id)}

    employees_filtered = [u for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE]
    if workspace_ids:
        employees_filtered = [e for e in employees_filtered if e.workspace_id in workspace_ids]

    all_employees = employees_filtered
    employees = employees_filtered
    if user_id:
        employees = [e for e in employees_filtered if str(e.id) == str(user_id)]
        if not employees:
            return None

    employee_ids = [e.id for e in employees]
    employee_map = {e.id: e for e in employees}

    periods = {}
    for key in ("today", "week", "month"):
        periods[key] = build_metrics_summary(
            actor=actor,
            period=key,
            workspace_id=workspace_id,
            user_id=user_id,
        )

    today_start, _ = period_bounds("today")
    emp_stats = _employee_metrics(actor.tenant_id, employee_ids, workspace_ids, today_start, today_start)

    employees_table = []
    for stat in emp_stats:
        emp = employee_map.get(stat["user_id"])
        if not emp:
            continue
        status = _status_for_employee(stat["calls"], stat.get("quality_score"))
        status_labels = {"ok": "Норма", "warn": "Контроль", "risk": "Риск"}
        employees_table.append(
            {
                "id": str(emp.id),
                "full_name": emp.full_name,
                "calls": stat["calls"],
                "quality_score": stat["quality_score"],
                "status": status,
                "status_label": status_labels[status],
            }
        )

    today_metrics = periods["today"]
    hero_calls = today_metrics["metrics"]["calls"]["value"] if today_metrics else 0
    hero_quality = today_metrics["metrics"]["quality_score"]["value"] if today_metrics else None

    ai_summary = _build_ai_summary(
        metrics_today=today_metrics,
        employees_table=employees_table,
        completeness=today_metrics["completeness"] if today_metrics else "empty",
    )

    return {
        "filters": {
            "workspaces": [{"id": str(w.id), "name": w.name} for w in workspaces],
            "employees": [{"id": str(e.id), "full_name": e.full_name} for e in all_employees],
            "workspace_id": workspace_id,
            "user_id": user_id,
        },
        "periods": periods,
        "hero": {
            "calls": hero_calls,
            "quality_score": hero_quality,
            "quality_available": today_metrics["metrics"]["quality_score"]["available"] if today_metrics else False,
            "plan_calls": float(PLAN_CALLS_PER_DAY * max(len(employee_ids), 1)),
            "plan_quality": float(PLAN_QUALITY),
        },
        "employees": employees_table,
        "ai_summary": ai_summary,
        "trend": _trend_series(actor.tenant_id, employee_ids, workspace_ids),
        "attention": {
            "count": len([e for e in employees_table if e["status"] != "ok"]),
            "text": (
                f"{len([e for e in employees_table if e['status'] != 'ok'])} сотрудника с просадкой за сегодня."
                if employees_table
                else None
            ),
        },
    }


def clients_queryset(actor: User, *, workspace_id: str | None = None, employee_id: str | None = None, status: str | None = None):
    qs = ClientToReview.objects.filter(tenant_id=actor.tenant_id).select_related("employee", "workspace")
    if actor.role == User.Role.EMPLOYEE:
        return qs.none()

    employee_ids = [u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE]
    qs = qs.filter(employee_id__in=employee_ids)

    if workspace_id:
        qs = qs.filter(workspace_id=workspace_id)
    if employee_id:
        qs = qs.filter(employee_id=employee_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def can_access_client(actor: User, client: ClientToReview) -> bool:
    return user_in_scope(actor, client.employee)
