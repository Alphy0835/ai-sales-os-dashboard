from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ModulePermission, Tenant, User, Workspace


class AuthCookieRefreshLogoutTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Auth Co", slug="auth-test")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="ОП Москва")
        self.user = User.objects.create_user(
            email="user@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Test User",
            role=User.Role.EMPLOYEE,
        )
        for module in ModulePermission.Module.values:
            ModulePermission.objects.update_or_create(
                user=self.user,
                module=module,
                defaults={"level": ModulePermission.Level.VIEW if module == ModulePermission.Module.DASHBOARD else ModulePermission.Level.NONE},
            )
        self.client = APIClient()

    def _login(self):
        return self.client.post(
            "/api/v1/auth/login/",
            {"email": "user@test.local", "password": "pass1234"},
            format="json",
        )

    def test_refresh_via_cookie_only(self):
        login = self._login()
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        refresh_value = login.cookies["refresh_token"].value

        self.client.credentials()
        self.client.cookies.clear()
        self.client.cookies["refresh_token"] = refresh_value

        refreshed = self.client.post("/api/v1/auth/refresh/", {}, format="json")
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn("access", refreshed.data)
        self.assertIn("access_token", refreshed.cookies)
        self.assertIn("refresh_token", refreshed.cookies)

        self.client.cookies["access_token"] = refreshed.cookies["access_token"].value
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["email"], "user@test.local")

    def test_logout_blacklists_refresh_token(self):
        login = self._login()
        refresh_value = login.cookies["refresh_token"].value

        self.client.cookies["refresh_token"] = refresh_value
        logout = self.client.post("/api/v1/auth/logout/", format="json")
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)

        self.client.credentials()
        self.client.cookies.clear()
        self.client.cookies["refresh_token"] = refresh_value
        denied = self.client.post("/api/v1/auth/refresh/", {}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_401_UNAUTHORIZED)
