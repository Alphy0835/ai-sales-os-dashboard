import json
import logging
import urllib.error
import urllib.request
from datetime import date, datetime, time, timezone as dt_timezone
from decimal import Decimal

from django.utils import timezone

from accounts.models import User
from integrations.models import IntegrationSource, MetricSnapshot
from integrations.services.crm_adapter import CrmAdapterError, decrypt_source_credentials

logger = logging.getLogger(__name__)


def _base_url(source: IntegrationSource, credentials: dict) -> str:
    subdomain = source.external_id or credentials.get("subdomain", "")
    if not subdomain:
        raise CrmAdapterError("amoCRM subdomain (external_id) is required")
    custom = credentials.get("base_url", "").rstrip("/")
    if custom:
        return custom
    return f"https://{subdomain}.amocrm.ru"


def _request_json(url: str, access_token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise CrmAdapterError(f"amoCRM HTTP {exc.code}: {detail[:200]}") from exc
    except urllib.error.URLError as exc:
        raise CrmAdapterError(f"amoCRM request failed: {exc.reason}") from exc


def _resolve_amocrm_user_id(source: IntegrationSource, employee: User, credentials: dict, base: str) -> int | None:
    if employee.external_id:
        try:
            return int(employee.external_id)
        except ValueError:
            pass

    token = credentials.get("access_token", "")
    if not token:
        return None

    cache_key = "_user_email_map"
    user_map = source.config_json.get(cache_key)
    if not user_map:
        data = _request_json(f"{base}/api/v4/users", token)
        user_map = {}
        for user in data.get("_embedded", {}).get("users", []):
            email = (user.get("email") or "").lower()
            if email:
                user_map[email] = user.get("id")
        config = dict(source.config_json or {})
        config[cache_key] = user_map
        source.config_json = config
        source.save(update_fields=["config_json"])

    return user_map.get(employee.email.lower())


def fetch_amocrm_employee_metrics(
    source: IntegrationSource,
    employee: User,
    period_date: date,
) -> dict[str, Decimal]:
    credentials = decrypt_source_credentials(source)
    token = credentials.get("access_token", "")
    if not token:
        raise CrmAdapterError("amoCRM access_token missing")

    base = _base_url(source, credentials)
    user_id = _resolve_amocrm_user_id(source, employee, credentials, base)
    if user_id is None:
        return {}

    start = datetime.combine(period_date, time.min, tzinfo=dt_timezone.utc)
    end = datetime.combine(period_date, time.max, tzinfo=dt_timezone.utc)
    ts_from = int(start.timestamp())
    ts_to = int(end.timestamp())

    won_status_ids = source.config_json.get("won_status_ids", [])
    params = (
        f"filter[responsible_user_id]={user_id}"
        f"&filter[closed_at][from]={ts_from}"
        f"&filter[closed_at][to]={ts_to}"
        f"&limit=250"
    )
    data = _request_json(f"{base}/api/v4/leads?{params}", token)
    leads = data.get("_embedded", {}).get("leads", [])

    deals = Decimal("0")
    revenue = Decimal("0")
    for lead in leads:
        status_id = lead.get("status_id")
        if won_status_ids and status_id not in won_status_ids:
            continue
        if not won_status_ids and lead.get("closed_at") is None:
            continue
        deals += 1
        price = lead.get("price") or 0
        revenue += Decimal(str(price))

    return {"deals": deals, "revenue": revenue}


def sync_amocrm_metrics(source: IntegrationSource) -> None:
    credentials = decrypt_source_credentials(source)
    if not credentials.get("access_token"):
        source.status = IntegrationSource.Status.ERROR
        source.last_error = "Missing amoCRM access_token"
        source.last_sync_at = timezone.now()
        source.save(update_fields=["status", "last_error", "last_sync_at"])
        return

    today = timezone.localdate()
    employees = User.objects.filter(
        tenant_id=source.tenant_id,
        role=User.Role.EMPLOYEE,
        is_active=True,
    )
    if source.workspace_id:
        employees = employees.filter(workspace_id=source.workspace_id)

    try:
        for employee in employees:
            metrics = fetch_amocrm_employee_metrics(source, employee, today)
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
        source.status = IntegrationSource.Status.CONNECTED
        source.last_error = ""
        source.last_sync_at = timezone.now()
        source.save(update_fields=["status", "last_error", "last_sync_at"])
    except CrmAdapterError as exc:
        logger.warning("amoCRM sync failed for source %s: %s", source.id, exc)
        source.status = IntegrationSource.Status.ERROR
        source.last_error = str(exc)[:500]
        source.last_sync_at = timezone.now()
        source.save(update_fields=["status", "last_error", "last_sync_at"])
