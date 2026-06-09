from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import RegistrationInvite, Tenant, User, Workspace


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
