from django.conf import settings
from django.utils import timezone

from integrations.models import IntegrationSource


def crm_sync_interval_minutes() -> int:
    return getattr(settings, "CRM_SYNC_INTERVAL_MINUTES", 60)


def crm_stale_threshold_minutes() -> int:
    return crm_sync_interval_minutes() * 2


def is_crm_source_stale(source: IntegrationSource) -> bool:
    if source.source_type != IntegrationSource.SourceType.CRM:
        return False
    if source.last_sync_at is None:
        return True
    elapsed = timezone.now() - source.last_sync_at
    return elapsed >= timezone.timedelta(minutes=crm_stale_threshold_minutes())


def crm_stale_reason(source: IntegrationSource) -> str | None:
    if not is_crm_source_stale(source):
        return None
    if source.last_sync_at is None:
        return "Синхронизация CRM ещё не выполнялась"
    elapsed = timezone.now() - source.last_sync_at
    minutes = int(elapsed.total_seconds() // 60)
    interval = crm_sync_interval_minutes()
    return (
        f"Данные CRM устарели: последняя синхронизация была {minutes} мин. назад "
        f"(ожидается не реже чем каждые {interval} мин.)"
    )
