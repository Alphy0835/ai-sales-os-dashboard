from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Tenant, User, Workspace
from accounts.services.password_reset import encode_uid, make_reset_token
from accounts.views import PasswordResetRateThrottle


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "accounts.authentication.CookieJWTAuthentication",
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
        "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_THROTTLE_RATES": {"login": None, "agent": None, "password_reset": None},
    },
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://localhost:3000",
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Reset Co", slug="reset-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Main")
        self.user = User.objects.create_user(
            email="user@test.local",
            password="oldpass123",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Reset User",
            role=User.Role.EMPLOYEE,
        )
        self.client = APIClient()

    def test_request_returns_200_for_existing_user(self):
        response = self.client.post(
            "/api/v1/auth/password-reset/",
            {"email": "user@test.local"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset-password", mail.outbox[0].body)

    def test_request_returns_200_for_unknown_email(self):
        response = self.client.post(
            "/api/v1/auth/password-reset/",
            {"email": "missing@test.local"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_request_skips_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            "/api/v1/auth/password-reset/",
            {"email": "user@test.local"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_request_logs_reset_link_for_console_backend(self):
        with patch("accounts.services.password_reset.logger") as mock_logger:
            response = self.client.post(
                "/api/v1/auth/password-reset/",
                {"email": "user@test.local"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_logger.info.assert_called_once()
        logged_url = mock_logger.info.call_args[0][2]
        self.assertIn("/reset-password?uid=", logged_url)

    def test_confirm_with_uid_sets_new_password(self):
        uid = encode_uid(self.user)
        token = make_reset_token(self.user)
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "newpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "user@test.local", "password": "newpass123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_confirm_with_email_sets_new_password(self):
        token = make_reset_token(self.user)
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"email": "user@test.local", "token": token, "new_password": "newpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

    def test_confirm_rejects_invalid_token(self):
        uid = encode_uid(self.user)
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": "invalid-token", "new_password": "newpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)
        token_error = response.data["token"]
        if isinstance(token_error, list):
            token_error = token_error[0]
        self.assertIn("Недействительная", str(token_error))

    def test_confirm_requires_uid_or_email(self):
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"token": "x", "new_password": "newpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "accounts.authentication.CookieJWTAuthentication",
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
        "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_THROTTLE_RATES": {"login": None, "agent": None, "password_reset": "2/min"},
    },
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PasswordResetThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        PasswordResetRateThrottle.rate = "2/min"
        self.client = APIClient()

    def tearDown(self):
        PasswordResetRateThrottle.rate = None
        cache.clear()

    def test_password_reset_returns_429_when_throttled(self):
        payload = {"email": "any@test.local"}
        for _ in range(2):
            response = self.client.post("/api/v1/auth/password-reset/", payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        throttled = self.client.post("/api/v1/auth/password-reset/", payload, format="json")
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
