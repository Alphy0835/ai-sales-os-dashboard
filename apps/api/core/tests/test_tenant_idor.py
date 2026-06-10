from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from ai.models import AnalyticsReport, CustomReport, KnowledgeArticle
from ai.services.agent import generate_agent_reply
from analytics.models import ClientToReview
from integrations.models import ConversationRecording, CrmLead, IntegrationSource, Transcription
from reviews.models import Review, ReviewTask


class CrossTenantIdorTests(TestCase):
    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="Tenant A", slug="tenant-a")
        self.tenant_b = Tenant.objects.create(name="Tenant B", slug="tenant-b")
        self.ws_a = Workspace.objects.create(tenant=self.tenant_a, name="A Москва")
        self.ws_b = Workspace.objects.create(tenant=self.tenant_b, name="B Москва")

        self.manager_a = self._create_manager("mgr-a@test.local", self.tenant_a, self.ws_a)
        self.manager_b = self._create_manager("mgr-b@test.local", self.tenant_b, self.ws_b)
        self.employee_a = User.objects.create_user(
            email="emp-a@test.local",
            password="pass1234",
            tenant=self.tenant_a,
            workspace=self.ws_a,
            full_name="Employee A",
            role=User.Role.EMPLOYEE,
        )
        self.employee_b = User.objects.create_user(
            email="emp-b@test.local",
            password="pass1234",
            tenant=self.tenant_b,
            workspace=self.ws_b,
            full_name="Employee B",
            role=User.Role.EMPLOYEE,
        )

        self.foreign_recording = ConversationRecording.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            employee=self.employee_b,
            source_kind=ConversationRecording.SourceKind.MANUAL,
            client_name="Foreign Client",
            status=ConversationRecording.Status.READY,
        )
        Transcription.objects.create(
            recording=self.foreign_recording,
            text="Secret transcript",
            status=Transcription.Status.COMPLETED,
        )
        self.foreign_client = ClientToReview.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            employee=self.employee_b,
            client_name="Foreign Corp",
            reason="Needs review",
            priority=ClientToReview.Priority.HIGH,
            status=ClientToReview.Status.NEW,
        )
        self.foreign_source = IntegrationSource.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            source_type=IntegrationSource.SourceType.CRM,
            name="Foreign CRM",
            status=IntegrationSource.Status.CONNECTED,
            config_json={"provider": "google_sheets"},
            last_sync_at=timezone.now(),
        )
        CrmLead.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            integration_source=self.foreign_source,
            external_lead_id="FB-1",
            client_name="Foreign Secret Corp",
            pipeline_stage="Closing",
            status_stage="open",
            manager_email="emp-b@test.local",
            employee=self.employee_b,
        )
        self.local_source = IntegrationSource.objects.create(
            tenant=self.tenant_a,
            workspace=self.ws_a,
            source_type=IntegrationSource.SourceType.CRM,
            name="Local CRM",
            status=IntegrationSource.Status.CONNECTED,
            config_json={"provider": "google_sheets"},
            last_sync_at=timezone.now(),
        )
        CrmLead.objects.create(
            tenant=self.tenant_a,
            workspace=self.ws_a,
            integration_source=self.local_source,
            external_lead_id="LA-1",
            client_name="Local Client",
            pipeline_stage="Qualification",
            status_stage="open",
            manager_email="emp-a@test.local",
            employee=self.employee_a,
        )
        self.foreign_review = Review.objects.create(
            tenant=self.tenant_b,
            workspace=self.ws_b,
            employee=self.employee_b,
            author=self.manager_b,
            comment="Foreign review secret",
            client_to_review=self.foreign_client,
        )
        self.foreign_task = ReviewTask.objects.create(
            review=self.foreign_review,
            title="Foreign task",
        )
        self.foreign_article = KnowledgeArticle.objects.create(
            tenant=self.tenant_b,
            title="ForeignSecretArticle",
            category=KnowledgeArticle.Category.PRODUCT,
            content="Foreign secret knowledge content",
            access_level=KnowledgeArticle.AccessLevel.ALL,
        )
        self.foreign_report = AnalyticsReport.objects.create(
            tenant=self.tenant_b,
            author=self.manager_b,
            workspace=self.ws_b,
            employee=self.employee_b,
            template=AnalyticsReport.Template.STANDARD_QUALITY,
            status=AnalyticsReport.Status.COMPLETED,
            summary_text="ForeignSecretReportSummary",
        )
        self.foreign_custom_report = CustomReport.objects.create(
            tenant=self.tenant_b,
            author=self.manager_b,
            title="Foreign custom report",
            description="Secret custom report",
            structured_query={"focus_stages": ["greeting"]},
        )

        self.client = APIClient()
        self._login(self.manager_a)

    def _create_manager(self, email, tenant, workspace):
        manager = User.objects.create_user(
            email=email,
            password="pass1234",
            tenant=tenant,
            workspace=workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=manager, workspace=workspace)
        for module in ModulePermission.Module.values:
            level = ModulePermission.Level.NONE
            if module in (
                ModulePermission.Module.DASHBOARD,
                ModulePermission.Module.REVIEWS,
            ):
                level = ModulePermission.Level.EDIT
            ModulePermission.objects.update_or_create(
                user=manager, module=module, defaults={"level": level}
            )
        return manager

    def _grant(self, user, **modules):
        for module, level in modules.items():
            ModulePermission.objects.update_or_create(
                user=user, module=module, defaults={"level": level}
            )

    def _login(self, user):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "pass1234"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_foreign_recording_detail_returns_404(self):
        response = self.client.get(f"/api/v1/integrations/recordings/{self.foreign_recording.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_foreign_recording_transcription_returns_404(self):
        response = self.client.get(
            f"/api/v1/integrations/recordings/{self.foreign_recording.id}/transcription/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_foreign_client_id_rejected_on_review_create(self):
        response = self.client.post(
            "/api/v1/manager/reviews/",
            {
                "employee_id": str(self.employee_a.id),
                "workspace_id": str(self.ws_a.id),
                "client_id": str(self.foreign_client.id),
                "comment": "Cross-tenant attempt",
                "tasks": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("client_id", response.data)

    @override_settings(CRM_SYNC_INTERVAL_MINUTES=60)
    @patch("ai.services.agent.maybe_refresh_crm")
    def test_cross_tenant_crm_lead_not_exposed_via_agent(self, mock_refresh):
        reply, _, _ = generate_agent_reply(
            actor=self.manager_a,
            message="Покажи список клиентов Foreign Secret Corp",
        )
        self.assertNotIn("Foreign Secret Corp", reply)
        mock_refresh.assert_called_once()

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("integrations.views.sync_integration_source.delay")
    def test_foreign_integration_source_sync_returns_404(self, mock_delay):
        ModulePermission.objects.update_or_create(
            user=self.manager_a,
            module=ModulePermission.Module.SETTINGS,
            defaults={"level": ModulePermission.Level.EDIT},
        )
        response = self.client.post(
            f"/api/v1/integrations/sources/{self.foreign_source.id}/sync/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_delay.assert_not_called()

    def test_foreign_user_id_on_manager_dashboard_returns_404(self):
        response = self.client.get(f"/api/v1/manager/dashboard/?user_id={self.employee_b.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_clients_excludes_foreign_tenant_clients(self):
        response = self.client.get("/api/v1/manager/clients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        client_ids = {row["id"] for row in response.data["results"]}
        self.assertNotIn(str(self.foreign_client.id), client_ids)
        client_names = {row["client_name"] for row in response.data["results"]}
        self.assertNotIn("Foreign Corp", client_names)

    def test_manager_clients_foreign_employee_filter_returns_empty(self):
        response = self.client.get(f"/api/v1/manager/clients/?employee_id={self.employee_b.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_manager_reviews_excludes_foreign_tenant_reviews(self):
        response = self.client.get("/api/v1/manager/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review_ids = {row["id"] for row in response.data["results"]}
        self.assertNotIn(str(self.foreign_review.id), review_ids)

    def test_manager_reviews_foreign_employee_filter_returns_empty(self):
        response = self.client.get(f"/api/v1/manager/reviews/?employee_id={self.employee_b.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_foreign_review_task_patch_returns_404(self):
        self._login(self.employee_a)
        response = self.client.patch(
            f"/api/v1/employee/tasks/{self.foreign_task.id}/",
            {"status": ReviewTask.Status.DONE},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_analytics_reports_list_excludes_foreign_tenant(self):
        self._grant(self.manager_a, analytics=ModulePermission.Level.VIEW)
        response = self.client.get("/api/v1/manager/analytics/reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report_ids = {row["id"] for row in response.data["results"]}
        self.assertNotIn(str(self.foreign_report.id), report_ids)
        summaries = {row.get("summary_text", "") for row in response.data["results"]}
        self.assertNotIn("ForeignSecretReportSummary", summaries)

    def test_analytics_report_run_rejects_foreign_workspace(self):
        self._grant(self.manager_a, analytics=ModulePermission.Level.RUN)
        response = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {"workspace_id": str(self.ws_b.id)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analytics_report_run_rejects_foreign_employee(self):
        self._grant(self.manager_a, analytics=ModulePermission.Level.RUN)
        response = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.ws_a.id),
                "employee_id": str(self.employee_b.id),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analytics_report_run_rejects_foreign_custom_report(self):
        self._grant(self.manager_a, analytics=ModulePermission.Level.RUN)
        response = self.client.post(
            "/api/v1/manager/analytics/reports/run/",
            {
                "workspace_id": str(self.ws_a.id),
                "custom_report_id": str(self.foreign_custom_report.id),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("custom_report_id", response.data)

    def test_knowledge_list_excludes_foreign_tenant_articles(self):
        self._grant(self.manager_a, settings=ModulePermission.Level.VIEW)
        response = self.client.get("/api/v1/manager/settings/knowledge/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {row["title"] for row in response.data["results"]}
        self.assertNotIn("ForeignSecretArticle", titles)

    def test_foreign_knowledge_article_patch_returns_404(self):
        self._grant(self.manager_a, settings=ModulePermission.Level.EDIT)
        response = self.client.patch(
            f"/api/v1/manager/settings/knowledge/{self.foreign_article.id}/",
            {"title": "Hijacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.foreign_article.refresh_from_db()
        self.assertEqual(self.foreign_article.title, "ForeignSecretArticle")

    def test_manager_cannot_access_employee_dashboard(self):
        response = self.client.get("/api/v1/employee/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_chat_does_not_leak_foreign_recording(self):
        self._grant(self.manager_a, agent=ModulePermission.Level.USE)
        response = self.client.post(
            "/api/v1/manager/agent/chat/",
            {
                "message": "Подскажи следующий шаг по переговорам",
                "client_name": "Foreign Client",
                "client_note": "Разбор звонка",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assistant = [m for m in response.data["messages"] if m["role"] == "assistant"][-1]
        self.assertNotIn("Secret transcript", assistant["content"])
