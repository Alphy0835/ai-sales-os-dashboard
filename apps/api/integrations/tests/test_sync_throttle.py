from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Tenant, Workspace
from integrations.models import IntegrationSource
from integrations.tasks import should_sync_source


@override_settings(CRM_SYNC_INTERVAL_MINUTES=60)
class SyncThrottleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Throttle Co", slug="throttle-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
            is_enabled=True,
            config_json={"provider": "google_sheets"},
        )

    def test_should_sync_when_never_synced(self):
        self.assertTrue(should_sync_source(self.source))

    def test_should_not_sync_within_interval(self):
        self.source.last_sync_at = timezone.now() - timedelta(minutes=10)
        self.source.save(update_fields=["last_sync_at"])
        self.assertFalse(should_sync_source(self.source))

    def test_should_sync_after_interval(self):
        self.source.last_sync_at = timezone.now() - timedelta(minutes=61)
        self.source.save(update_fields=["last_sync_at"])
        self.assertTrue(should_sync_source(self.source))

    def test_force_bypasses_throttle(self):
        self.source.last_sync_at = timezone.now()
        self.source.save(update_fields=["last_sync_at"])
        self.assertTrue(should_sync_source(self.source, force=True))

    def test_disabled_source_not_synced(self):
        self.source.is_enabled = False
        self.source.save(update_fields=["is_enabled"])
        self.assertFalse(should_sync_source(self.source))
