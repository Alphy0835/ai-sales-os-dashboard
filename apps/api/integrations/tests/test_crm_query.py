from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import ManagerScope, Tenant, User, Workspace
from analytics.models import ClientToReview
from integrations.models import CrmLead, IntegrationSource
from integrations.services.crm.query import CrmQueryFilters, query_crm_leads, resolve_vocabulary


@override_settings(CRM_SYNC_INTERVAL_MINUTES=60)
class CrmQueryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Query Co", slug="query-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.manager = User.objects.create_user(
            email="mgr@query.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        self.employee = User.objects.create_user(
            email="emp@query.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        self.other_employee = User.objects.create_user(
            email="other@query.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Other",
            role=User.Role.EMPLOYEE,
        )
        self.source = IntegrationSource.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name="CRM",
            status=IntegrationSource.Status.CONNECTED,
            config_json={
                "provider": "google_sheets",
                "crm_vocabulary": {
                    "stages": {"Closing": ["closing", "дожатие"]},
                    "statuses": {"open": ["open", "в работе"]},
                },
            },
            last_sync_at=timezone.now(),
        )
        CrmLead.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            integration_source=self.source,
            external_lead_id="L-1",
            client_name="Alpha Corp",
            pipeline_stage="Closing",
            status_stage="open",
            manager_email="emp@query.local",
            employee=self.employee,
        )
        CrmLead.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            integration_source=self.source,
            external_lead_id="L-2",
            client_name="Beta LLC",
            pipeline_stage="Qualification",
            status_stage="done",
            manager_email="other@query.local",
            employee=self.other_employee,
        )
        ClientToReview.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            client_external_id="L-1",
            client_name="Alpha Corp",
            reason="Needs review",
        )

    def test_count_all_scoped_leads_for_manager(self):
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(),
            mode="count",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 2)
        self.assertIsNotNone(result["as_of"])

    def test_employee_sees_only_own_leads(self):
        result = query_crm_leads(
            self.employee,
            filters=CrmQueryFilters(),
            mode="count",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)

    def test_pipeline_stage_vocabulary_filter(self):
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(pipeline_stage="дожатие"),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["leads"][0]["client_name"], "Alpha Corp")

    def test_search_filter(self):
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(search="Alpha"),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)

    def test_needs_review_filter(self):
        result = query_crm_leads(
            self.manager,
            filters=CrmQueryFilters(needs_review=True),
            mode="list",
            integration_source=self.source,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["leads"][0]["external_lead_id"], "L-1")

    def test_resolve_vocabulary_aliases(self):
        resolved = resolve_vocabulary(self.source, "stages", "closing")
        self.assertEqual(resolved, "Closing")
        status = resolve_vocabulary(self.source, "statuses", "в работе")
        self.assertEqual(status, "open")
