from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Tenant, User, Workspace
from integrations.models import IntegrationSource
from integrations.services.aggregation import build_metrics_summary, source_health
from integrations.services.health import crm_stale_reason, is_crm_source_stale
from integrations.tasks import sync_all_sources


@override_settings(CRM_SYNC_INTERVAL_MINUTES=60)
class SourceStaleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Stale Co", slug="stale-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.crm = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
            is_enabled=True,
            config_json={"provider": "google_sheets"},
        )
        self.telephony = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.TELEPHONY,
            name="Tel",
            status=IntegrationSource.Status.CONNECTED,
            is_enabled=True,
        )
        self.manager = User.objects.create_user(
            email="mgr@stale.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )

    def test_never_synced_crm_is_stale(self):
        self.assertTrue(is_crm_source_stale(self.crm))
        self.assertEqual(crm_stale_reason(self.crm), "Синхронизация CRM ещё не выполнялась")

    def test_fresh_crm_not_stale(self):
        self.crm.last_sync_at = timezone.now() - timedelta(minutes=30)
        self.crm.save(update_fields=["last_sync_at"])
        self.assertFalse(is_crm_source_stale(self.crm))
        self.assertIsNone(crm_stale_reason(self.crm))

    def test_crm_stale_after_double_interval(self):
        self.crm.last_sync_at = timezone.now() - timedelta(minutes=121)
        self.crm.save(update_fields=["last_sync_at"])
        self.assertTrue(is_crm_source_stale(self.crm))
        reason = crm_stale_reason(self.crm)
        self.assertIn("Данные CRM устарели", reason)
        self.assertIn("60 мин.", reason)

    def test_telephony_never_marked_stale(self):
        self.assertFalse(is_crm_source_stale(self.telephony))
        self.assertIsNone(crm_stale_reason(self.telephony))

    def test_source_health_includes_stale_fields(self):
        self.crm.last_sync_at = timezone.now() - timedelta(minutes=121)
        self.crm.save(update_fields=["last_sync_at"])
        health = source_health([self.crm, self.telephony])
        crm_entry = next(item for item in health if item["source_type"] == "crm")
        tel_entry = next(item for item in health if item["source_type"] == "telephony")
        self.assertTrue(crm_entry["stale"])
        self.assertIn("Данные CRM устарели", crm_entry["stale_reason"])
        self.assertFalse(tel_entry["stale"])
        self.assertIsNone(tel_entry["stale_reason"])

    def test_build_metrics_summary_exposes_stale(self):
        self.crm.last_sync_at = timezone.now() - timedelta(minutes=121)
        self.crm.save(update_fields=["last_sync_at"])
        summary = build_metrics_summary(actor=self.manager, period="today")
        crm_entry = next(item for item in summary["sources"] if item["source_type"] == "crm")
        self.assertTrue(crm_entry["stale"])
        self.assertIsNotNone(crm_entry["stale_reason"])

    @patch("integrations.tasks.sync_integration_source.delay")
    def test_sync_all_sources_logs_throttle_vs_stale(self, mock_delay):
        IntegrationSource.objects.filter(tenant=self.tenant).update(is_enabled=False)
        fresh = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="Fresh CRM",
            status=IntegrationSource.Status.CONNECTED,
            is_enabled=True,
            last_sync_at=timezone.now() - timedelta(minutes=10),
        )
        stale = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="Stale CRM",
            status=IntegrationSource.Status.CONNECTED,
            is_enabled=True,
            last_sync_at=timezone.now() - timedelta(minutes=121),
        )
        with self.assertLogs("integrations.tasks", level="INFO") as captured:
            result = sync_all_sources()
        self.assertEqual(result["queued"], 1)
        messages = [record.getMessage() for record in captured.records]
        self.assertTrue(any("throttled" in message and str(fresh.id) in message for message in messages))
        self.assertTrue(any("stale" in message.lower() and str(stale.id) in message for message in messages))
        mock_delay.assert_called_once_with(str(stale.id))
