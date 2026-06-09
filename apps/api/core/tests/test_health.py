from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse


class HealthEndpointTests(TestCase):
    def test_liveness_returns_200(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "ai-sales-os-api")

    @patch("core.views.check_celery", return_value=(True, None))
    @patch("core.views.check_redis", return_value=(True, None))
    @patch("core.views.check_database", return_value=(True, None))
    def test_readiness_all_ok_returns_200(self, *_mocks):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "ai-sales-os-api")
        self.assertEqual(data["checks"]["database"]["status"], "ok")
        self.assertEqual(data["checks"]["redis"]["status"], "ok")
        self.assertEqual(data["checks"]["celery"]["status"], "ok")

    @patch("core.views.check_celery", return_value=(True, None))
    @patch("core.views.check_redis", return_value=(True, None))
    @patch("core.views.check_database", return_value=(False, "connection refused"))
    def test_readiness_database_fail_returns_503(self, *_mocks):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["checks"]["database"]["status"], "error")
        self.assertEqual(data["checks"]["database"]["error"], "connection refused")

    @patch("core.views.check_celery", return_value=(True, None))
    @patch("core.views.check_redis", return_value=(False, "timeout"))
    @patch("core.views.check_database", return_value=(True, None))
    def test_readiness_redis_fail_returns_503(self, *_mocks):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["checks"]["redis"]["status"], "error")
        self.assertEqual(data["checks"]["redis"]["error"], "timeout")

    @patch("core.views.check_celery", return_value=(False, "no workers responded"))
    @patch("core.views.check_redis", return_value=(True, None))
    @patch("core.views.check_database", return_value=(True, None))
    def test_readiness_celery_fail_returns_503(self, *_mocks):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["checks"]["celery"]["status"], "error")
        self.assertEqual(data["checks"]["celery"]["error"], "no workers responded")

    @override_settings(SECURE_SSL_REDIRECT=True)
    @patch("core.views.check_celery", return_value=(True, None))
    @patch("core.views.check_redis", return_value=(True, None))
    @patch("core.views.check_database", return_value=(True, None))
    def test_readiness_returns_200_without_ssl_redirect(self, *_mocks):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
