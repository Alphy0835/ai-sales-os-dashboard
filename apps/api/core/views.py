import logging

import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views import View

from config.celery import app

logger = logging.getLogger(__name__)


class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok", "service": "ai-sales-os-api"})


def check_database():
    try:
        connection.ensure_connection()
        return True, None
    except Exception as exc:
        logger.warning("readiness database check failed: %s", exc)
        return False, str(exc)


def check_redis():
    if not settings.CELERY_BROKER_URL:
        return True, None
    try:
        client = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        client.ping()
        return True, None
    except Exception as exc:
        logger.warning("readiness redis check failed: %s", exc)
        return False, str(exc)


def check_celery():
    if not settings.CELERY_BROKER_URL or settings.CELERY_TASK_ALWAYS_EAGER:
        return True, None
    try:
        result = app.control.inspect(timeout=2.0).ping()
        if result:
            return True, None
        return False, "no workers responded"
    except Exception as exc:
        logger.warning("readiness celery check failed: %s", exc)
        return False, str(exc)


class ReadinessView(View):
    def get(self, request):
        checks = {}
        all_ok = True

        for name, check_fn in (
            ("database", check_database),
            ("redis", check_redis),
            ("celery", check_celery),
        ):
            ok, error = check_fn()
            entry = {"status": "ok" if ok else "error"}
            if error:
                entry["error"] = error
            checks[name] = entry
            if not ok:
                all_ok = False

        return JsonResponse(
            {
                "status": "ok" if all_ok else "error",
                "service": "ai-sales-os-api",
                "checks": checks,
            },
            status=200 if all_ok else 503,
        )
