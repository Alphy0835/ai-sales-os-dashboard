from decimal import Decimal

from django.utils import timezone

from accounts.models import User
from integrations.models import IntegrationSource, MetricSnapshot


DEMO_METRICS = {
    IntegrationSource.SourceType.CRM: {"deals": Decimal("2"), "revenue": Decimal("150000")},
    IntegrationSource.SourceType.TELEPHONY: {"calls": Decimal("8"), "quality_score": Decimal("78")},
    IntegrationSource.SourceType.REPORTING: {"meetings": Decimal("3"), "revenue": Decimal("50000")},
}


def _run_demo_sync(source: IntegrationSource):
    today = timezone.localdate()
    employees = User.objects.filter(
        tenant_id=source.tenant_id,
        role=User.Role.EMPLOYEE,
        is_active=True,
    )
    if source.workspace_id:
        employees = employees.filter(workspace_id=source.workspace_id)

    if source.status in (IntegrationSource.Status.DISCONNECTED, IntegrationSource.Status.ERROR):
        source.last_sync_at = timezone.now()
        source.save(update_fields=["last_sync_at"])
        return

    metrics = DEMO_METRICS.get(source.source_type, {})
    if source.status == IntegrationSource.Status.DEGRADED:
        metrics = {k: v for k, v in metrics.items() if k != "quality_score"}

    for employee in employees:
        for metric_key, value in metrics.items():
            MetricSnapshot.objects.update_or_create(
                tenant_id=source.tenant_id,
                workspace_id=employee.workspace_id,
                user_id=employee.id,
                source=source,
                metric_key=metric_key,
                period_date=today,
                defaults={"value": value},
            )

    source.last_sync_at = timezone.now()
    source.last_error = ""
    source.save(update_fields=["last_sync_at", "last_error"])


def run_source_sync(source: IntegrationSource):
    if (
        source.source_type == IntegrationSource.SourceType.CRM
        and source.credentials_encrypted
    ):
        from integrations.services.crm_adapter import run_crm_sync

        run_crm_sync(source)
        return

    _run_demo_sync(source)
