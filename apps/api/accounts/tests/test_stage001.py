from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import AuditLog, ManagerScope, ModulePermission, Tenant, User, Workspace
from accounts.services.grant import PermissionGrantError, grant_permissions
from accounts.services.scope import get_accessible_users, user_in_scope


class Stage001TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", slug="test")
        self.moscow = Workspace.objects.create(tenant=self.tenant, name="ОП Москва")
        self.spb = Workspace.objects.create(tenant=self.tenant, name="ОП СПб")

        self.top = User.objects.create_user(
            email="top@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.moscow,
            full_name="Top Manager",
            role=User.Role.MANAGER,
        )
        ManagerScope.objects.create(user=self.top, workspace=self.moscow)
        ManagerScope.objects.create(user=self.top, workspace=self.spb)
        self._set_perms(self.top, settings=ModulePermission.Level.EDIT, reviews=ModulePermission.Level.EDIT)

        self.regional = User.objects.create_user(
            email="regional@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.moscow,
            full_name="Regional Manager",
            role=User.Role.MANAGER,
            manager=self.top,
        )
        ManagerScope.objects.create(user=self.regional, workspace=self.moscow)
        self._set_perms(
            self.regional,
            settings=ModulePermission.Level.EDIT,
            reviews=ModulePermission.Level.VIEW,
            agent=ModulePermission.Level.USE,
        )

        self.employee = User.objects.create_user(
            email="employee@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.moscow,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        self._set_perms(self.employee, dashboard=ModulePermission.Level.VIEW)

        self.spb_employee = User.objects.create_user(
            email="spb@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.spb,
            full_name="SPB Employee",
            role=User.Role.EMPLOYEE,
        )

        self.client = APIClient()

    def _set_perms(self, user, **modules):
        defaults = {m: ModulePermission.Level.NONE for m in ModulePermission.Module.values}
        defaults.update(modules)
        for module, level in defaults.items():
            ModulePermission.objects.update_or_create(
                user=user, module=module, defaults={"level": level}
            )

    def _login(self, email):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": email, "password": "pass1234"},
            format="json",
        )
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_login_sets_cookies_and_cookie_auth(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "regional@test.local", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

        self.client.credentials()
        self.client.cookies["access_token"] = response.cookies["access_token"].value
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["email"], "regional@test.local")

    def test_hierarchy_scope_isolation(self):
        regional_users = {u.email for u in get_accessible_users(self.regional)}
        self.assertIn("employee@test.local", regional_users)
        self.assertNotIn("spb@test.local", regional_users)
        self.assertNotIn("top@test.local", regional_users)

        self.assertTrue(user_in_scope(self.regional, self.employee))
        self.assertFalse(user_in_scope(self.regional, self.spb_employee))

    def test_scope_endpoint_denies_out_of_scope(self):
        self._login("regional@test.local")
        response = self.client.get(f"/api/v1/scope/users/{self.spb_employee.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.SCOPE_DENIED,
                actor=self.regional,
                target_user=self.spb_employee,
            ).exists()
        )

    def test_ceiling_rule_blocks_broader_grant(self):
        with self.assertRaises(PermissionGrantError) as ctx:
            grant_permissions(
                grantor=self.regional,
                target_user=self.employee,
                permissions={ModulePermission.Module.REVIEWS: ModulePermission.Level.EDIT},
            )
        self.assertEqual(ctx.exception.code, "ceiling_violation")

    def test_permission_grant_and_audit(self):
        grant_permissions(
            grantor=self.regional,
            target_user=self.employee,
            permissions={ModulePermission.Module.REVIEWS: ModulePermission.Level.VIEW},
        )
        perm = ModulePermission.objects.get(
            user=self.employee, module=ModulePermission.Module.REVIEWS
        )
        self.assertEqual(perm.level, ModulePermission.Level.VIEW)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.PERMISSION_CHANGE,
                actor=self.regional,
                target_user=self.employee,
                module=ModulePermission.Module.REVIEWS,
                new_level=ModulePermission.Level.VIEW,
            ).exists()
        )

    def test_permission_api_put(self):
        self._login("regional@test.local")
        response = self.client.put(
            f"/api/v1/permissions/users/{self.employee.id}/",
            {"permissions": {ModulePermission.Module.AGENT: ModulePermission.Level.USE}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(
            f"/api/v1/permissions/users/{self.employee.id}/",
            {"permissions": {ModulePermission.Module.REVIEWS: ModulePermission.Level.EDIT}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_audit_endpoint(self):
        grant_permissions(
            grantor=self.regional,
            target_user=self.employee,
            permissions={ModulePermission.Module.AGENT: ModulePermission.Level.USE},
        )
        self._login("regional@test.local")
        response = self.client.get("/api/v1/audit/permissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)
