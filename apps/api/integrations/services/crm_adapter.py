import json
import logging
from decimal import Decimal

from ai.services.crypto import decrypt_secret, encrypt_secret

from integrations.models import IntegrationSource

logger = logging.getLogger(__name__)


class CrmAdapterError(Exception):
    pass


def decrypt_source_credentials(source: IntegrationSource) -> dict:
    raw = source.credentials_encrypted or ""
    if not raw:
        return {}
    decrypted = decrypt_secret(raw)
    if not decrypted:
        return {}
    try:
        return json.loads(decrypted)
    except json.JSONDecodeError:
        return {}


def encrypt_source_credentials(credentials: dict) -> str:
    return encrypt_secret(json.dumps(credentials))


def run_crm_sync(source: IntegrationSource) -> None:
    if source.source_type != IntegrationSource.SourceType.CRM:
        return
    if not source.credentials_encrypted:
        return

    provider = (source.config_json or {}).get("provider", "amocrm")
    if provider != "amocrm":
        return

    from integrations.services.crm.amocrm import sync_amocrm_metrics

    sync_amocrm_metrics(source)


def fetch_employee_metrics(
    source: IntegrationSource,
    employee,
    period_date,
) -> dict[str, Decimal]:
    """Fetch CRM metrics for one employee on a given date."""
    from integrations.services.crm.amocrm import fetch_amocrm_employee_metrics

    return fetch_amocrm_employee_metrics(source, employee, period_date)
