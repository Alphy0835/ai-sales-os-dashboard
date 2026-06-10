from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import AuditLog, ManagerScope, ModulePermission, Tenant, User, Workspace
from analytics.models import ClientToReview
from reviews.models import Review, ReviewTask


class Stage004TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test-reviews")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="ОП Москва")

        self.manager = User.objects.create_user(
            email="mgr@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.manager, workspace=self.workspace)
        self._set_perms(self.manager, reviews=ModulePermission.Level.EDIT, dashboard=ModulePermission.Level.VIEW)

        self.view_only_manager = User.objects.create_user(
            email="viewmgr@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="View Manager",
            role=User.Role.MANAGER,
            manager=self.manager,
        )
        ManagerScope.objects.create(user=self.view_only_manager, workspace=self.workspace)
        self._set_perms(self.view_only_manager, reviews=ModulePermission.Level.VIEW, dashboard=ModulePermission.Level.VIEW)

        self.employee = User.objects.create_user(
            email="emp@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee One",
            role=User.Role.EMPLOYEE,
        )
        self._set_perms(self.employee, dashboard=ModulePermission.Level.VIEW)

        self.client_row = ClientToReview.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            client_name="Client A",
            reason="Low quality",
        )

        self.api = APIClient()

    def _set_perms(self, user, **modules):
        defaults = {m: ModulePermission.Level.NONE for m in ModulePermission.Module.values}
        defaults.update(modules)
        for module, level in defaults.items():
            ModulePermission.objects.update_or_create(
                user=user, module=module, defaults={"level": level}
            )

    def _login(self, email):
        response = self.api.post(
            "/api/v1/auth/login/",
            {"email": email, "password": "pass1234"},
            format="json",
        )
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_manager_creates_review_with_tasks_and_audit(self):
        self._login("mgr@test.local")
        response = self.api.post(
            "/api/v1/manager/reviews/",
            {
                "employee_id": str(self.employee.id),
                "workspace_id": str(self.workspace.id),
                "comment": "Разбор по качеству",
                "discussion": "Обсудили скрипт приветствия",
                "client_id": str(self.client_row.id),
                "tasks": ["Переслушать 3 звонка", "Обновить скрипт"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tasks_total"], 2)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.REVIEW_CREATE,
                target_user=self.employee,
                actor=self.manager,
            ).exists()
        )
        self.client_row.refresh_from_db()
        self.assertEqual(self.client_row.status, ClientToReview.Status.DONE)

    def test_reviewed_client_hidden_from_queue(self):
        self._login("mgr@test.local")
        self.api.post(
            "/api/v1/manager/reviews/",
            {
                "employee_id": str(self.employee.id),
                "workspace_id": str(self.workspace.id),
                "client_id": str(self.client_row.id),
                "comment": "Done",
                "tasks": [],
            },
            format="json",
        )
        listing = self.api.get("/api/v1/manager/clients/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 0)

    def test_view_only_manager_cannot_create(self):
        self._login("viewmgr@test.local")
        response = self.api.post(
            "/api/v1/manager/reviews/",
            {
                "employee_id": str(self.employee.id),
                "workspace_id": str(self.workspace.id),
                "comment": "Should fail",
                "tasks": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_lists_reviews_filtered_by_employee(self):
        Review.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            author=self.manager,
            comment="Existing",
        )
        self._login("mgr@test.local")
        response = self.api.get(f"/api/v1/manager/reviews/?employee_id={self.employee.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_employee_sees_tasks_on_dashboard_and_updates_status(self):
        review = Review.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            author=self.manager,
            comment="Review",
        )
        task = ReviewTask.objects.create(review=review, title="Task one")

        self._login("emp@test.local")
        patch = self.api.patch(
            f"/api/v1/employee/tasks/{task.id}/",
            {"status": ReviewTask.Status.DONE},
            format="json",
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data["status"], ReviewTask.Status.DONE)

        self._login("mgr@test.local")
        history = self.api.get("/api/v1/manager/reviews/")
        task_data = history.data["results"][0]["tasks"][0]
        self.assertEqual(task_data["status"], ReviewTask.Status.DONE)

    def test_employee_cannot_update_other_task(self):
        other = User.objects.create_user(
            email="other@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Other",
            role=User.Role.EMPLOYEE,
        )
        review = Review.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=other,
            author=self.manager,
            comment="Other review",
        )
        task = ReviewTask.objects.create(review=review, title="Not yours")

        self._login("emp@test.local")
        response = self.api.patch(
            f"/api/v1/employee/tasks/{task.id}/",
            {"status": ReviewTask.Status.DONE},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
