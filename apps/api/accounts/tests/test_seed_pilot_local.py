from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import ManagerScope, ModulePermission, RegistrationInvite, Tenant, User, Workspace
from analytics.models import ClientToReview
from integrations.config_templates import GOOGLE_SHEETS_CONFIG_TEMPLATE
from integrations.models import IntegrationSource, MetricSnapshot


class SeedPilotLocalCommandTests(TestCase):
    @override_settings(DEBUG=True)
    def test_seed_pilot_local_is_idempotent_and_creates_expected_objects(self):
        call_command("seed_pilot_local")
        call_command("seed_pilot_local")

        tenant = Tenant.objects.get(slug="pilot-local")
        workspace = Workspace.objects.get(tenant=tenant, name="Pilot Office")

        manager = User.objects.get(tenant=tenant, email="pilot-mgr@local.test")
        employee = User.objects.get(tenant=tenant, email="pilot-emp@local.test")

        self.assertEqual(manager.role, User.Role.MANAGER)
        self.assertTrue(manager.check_password("pilot1234"))
        self.assertEqual(employee.role, User.Role.EMPLOYEE)
        self.assertTrue(employee.check_password("pilot1234"))

        self.assertTrue(
            ManagerScope.objects.filter(user=manager, workspace=workspace).exists()
        )
        self.assertEqual(
            ModulePermission.objects.get(
                user=manager, module=ModulePermission.Module.REVIEWS
            ).level,
            ModulePermission.Level.EDIT,
        )
        self.assertEqual(
            ModulePermission.objects.get(
                user=employee, module=ModulePermission.Module.AGENT
            ).level,
            ModulePermission.Level.USE,
        )
        self.assertEqual(
            ModulePermission.objects.get(
                user=employee, module=ModulePermission.Module.CLIENTS
            ).level,
            ModulePermission.Level.NONE,
        )

        invite = RegistrationInvite.objects.get(code="PILOT-LOCAL-2026")
        self.assertEqual(invite.tenant_id, tenant.id)
        self.assertEqual(invite.workspace_id, workspace.id)
        self.assertEqual(invite.max_uses, 10)
        self.assertGreater(invite.expires_at, timezone.now() + timedelta(days=30))

        source = IntegrationSource.objects.get(
            tenant=tenant,
            workspace=workspace,
            name="Pilot Google Sheets",
        )
        self.assertEqual(source.source_type, IntegrationSource.SourceType.CRM)
        self.assertEqual(source.status, IntegrationSource.Status.CONNECTED)
        self.assertEqual(source.config_json.get("provider"), "google_sheets")
        self.assertEqual(
            source.config_json.get("review_rules"),
            GOOGLE_SHEETS_CONFIG_TEMPLATE["review_rules"],
        )
        self.assertEqual(source.credentials_encrypted, "")
        self.assertIsNotNone(source.last_sync_at)

        snapshot = MetricSnapshot.objects.get(
            tenant=tenant,
            user=employee,
            source=source,
            metric_key="deals",
        )
        self.assertEqual(snapshot.value, 5)

        reviews = ClientToReview.objects.filter(tenant=tenant, employee=employee)
        self.assertEqual(reviews.count(), 3)
        self.assertTrue(
            reviews.filter(
                client_external_id="PILOT-L-002",
                reason="Closing",
            ).exists()
        )
        self.assertFalse(
            reviews.filter(client_external_id="PILOT-L-003").exists()
        )
        self.assertFalse(
            reviews.filter(client_external_id="PILOT-L-005").exists()
        )

    @override_settings(DEBUG=False)
    def test_refuses_without_allow_flag_in_production_mode(self):
        with self.assertRaises(CommandError):
            call_command("seed_pilot_local")
