from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import ManagerScope, ModulePermission, RegistrationInvite, Tenant, User, Workspace
from accounts.services.default_permissions import EMPLOYEE_PERMISSIONS, MANAGER_PERMISSIONS


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "accounts.authentication.CookieJWTAuthentication",
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
        "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_THROTTLE_RATES": {"login": None, "agent": None},
    }
)
class RegistrationTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Invite Co", slug="invite-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Main")
        self.invite = RegistrationInvite.objects.create(
            code="TEST-INVITE-001",
            tenant=self.tenant,
            workspace=self.workspace,
            role=User.Role.EMPLOYEE,
            expires_at=timezone.now() + timedelta(days=7),
            max_uses=2,
        )
        self.client = APIClient()

    def _register_payload(self, **overrides):
        payload = {
            "email": "newuser@test.local",
            "password": "securepass1",
            "full_name": "New User",
            "invite_code": self.invite.code,
        }
        payload.update(overrides)
        return payload

    def test_register_creates_user_and_returns_tokens(self):
        response = self.client.post("/api/v1/auth/register/", self._register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "newuser@test.local")
        self.assertEqual(response.data["user"]["role"], User.Role.EMPLOYEE)
        self.assertEqual(response.cookies["access_token"].value, response.data["access"])

        user = User.objects.get(email="newuser@test.local")
        self.assertEqual(user.tenant_id, self.tenant.id)
        self.assertEqual(user.workspace_id, self.workspace.id)

        self.invite.refresh_from_db()
        self.assertEqual(self.invite.use_count, 1)
        self.assertIsNotNone(self.invite.used_at)

    def test_register_rejects_expired_invite(self):
        self.invite.expires_at = timezone.now() - timedelta(hours=1)
        self.invite.save(update_fields=["expires_at"])
        response = self.client.post("/api/v1/auth/register/", self._register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_register_rejects_max_uses_exceeded(self):
        self.invite.use_count = self.invite.max_uses
        self.invite.save(update_fields=["use_count"])
        response = self.client.post("/api/v1/auth/register/", self._register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_register_rejects_invite_without_workspace(self):
        invite = RegistrationInvite(
            code="NO-WORKSPACE",
            tenant=self.tenant,
            role=User.Role.EMPLOYEE,
            expires_at=timezone.now() + timedelta(days=7),
        )
        invite.save()
        response = self.client.post(
            "/api/v1/auth/register/",
            self._register_payload(invite_code="NO-WORKSPACE"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_register_rejects_invalid_invite_code(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            self._register_payload(invite_code="DOES-NOT-EXIST"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            email="existing@test.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Existing",
            role=User.Role.EMPLOYEE,
        )
        response = self.client.post(
            "/api/v1/auth/register/",
            self._register_payload(email="existing@test.local"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_allows_second_use_when_max_uses_gt_one(self):
        first = self.client.post("/api/v1/auth/register/", self._register_payload(), format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        second = self.client.post(
            "/api/v1/auth/register/",
            self._register_payload(email="second@test.local"),
            format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.use_count, 2)

    def test_invite_auto_generates_code_on_save_when_empty(self):
        invite = RegistrationInvite(
            tenant=self.tenant,
            workspace=self.workspace,
            role=User.Role.EMPLOYEE,
            expires_at=timezone.now() + timedelta(days=7),
        )
        invite.save()
        self.assertTrue(invite.code)
        self.assertGreaterEqual(len(invite.code), 16)

    def test_registration_invite_requires_workspace(self):
        from django.core.exceptions import ValidationError

        invite = RegistrationInvite(
            tenant=self.tenant,
            role=User.Role.MANAGER,
            expires_at=timezone.now() + timedelta(days=7),
        )
        with self.assertRaises(ValidationError):
            invite.full_clean()

    @override_settings(FRONTEND_URL="http://localhost:3000")
    def test_invite_registration_url_property(self):
        self.assertEqual(
            self.invite.registration_url,
            "http://localhost:3000/register?code=TEST-INVITE-001",
        )

    def test_register_applies_employee_default_permissions(self):
        response = self.client.post("/api/v1/auth/register/", self._register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="newuser@test.local")
        for module, expected_level in EMPLOYEE_PERMISSIONS.items():
            perm = ModulePermission.objects.get(user=user, module=module)
            self.assertEqual(perm.level, expected_level)
        self.assertFalse(ManagerScope.objects.filter(user=user).exists())

    def test_register_applies_manager_default_permissions_and_scope(self):
        self.invite.role = User.Role.MANAGER
        self.invite.save(update_fields=["role"])
        response = self.client.post(
            "/api/v1/auth/register/",
            self._register_payload(email="manager-new@test.local"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="manager-new@test.local")
        for module, expected_level in MANAGER_PERMISSIONS.items():
            perm = ModulePermission.objects.get(user=user, module=module)
            self.assertEqual(perm.level, expected_level)
        self.assertTrue(
            ManagerScope.objects.filter(user=user, workspace=self.workspace).exists()
        )

    def test_register_rejects_email_when_expected_email_set(self):
        self.invite.expected_email = "expected@test.local"
        self.invite.save(update_fields=["expected_email"])
        response = self.client.post("/api/v1/auth/register/", self._register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_accepts_matching_expected_email(self):
        self.invite.expected_email = "newuser@test.local"
        self.invite.save(update_fields=["expected_email"])
        response = self.client.post("/api/v1/auth/register/", self._register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
