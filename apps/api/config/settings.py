import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

TESTING = "test" in sys.argv


def _env_bool(name: str, default: bool | None = None) -> bool | None:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in ("true", "1", "yes")


_django_env = os.environ.get("DJANGO_ENV", "").strip().lower()
_debug_env = os.environ.get("DJANGO_DEBUG")
IS_PRODUCTION = _django_env == "production" or (
    _debug_env is not None and _debug_env.lower() == "false"
)
USE_HTTPS_SETTINGS = IS_PRODUCTION or bool(_env_bool("DJANGO_SECURE", False))

if IS_PRODUCTION and not TESTING:
    SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
    if len(SECRET_KEY) < 32:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY environment variable is required in production "
            "and must be at least 32 characters."
        )
else:
    SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")

if IS_PRODUCTION:
    DEBUG = bool(_env_bool("DJANGO_DEBUG", False))
else:
    DEBUG = bool(_env_bool("DJANGO_DEBUG", True))
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "core",
    "accounts",
    "integrations",
    "analytics",
    "reviews",
    "ai",
]

MIDDLEWARE = [
    "core.middleware.SecureProxySecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
if IS_PRODUCTION:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

if USE_HTTPS_SETTINGS:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

# Same-origin BFF (Next.js rewrites /api/v1 → Django): cookie auth uses SameSite=Lax;
# no CSRF token needed for JWT cookie API calls from the same site. Cross-origin
# admin/API clients should list origins here if using session auth.
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000"),
    ).split(",")
    if o.strip()
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Rate=None disables the throttle (used in tests).
    "DEFAULT_THROTTLE_RATES": {
        "login": None if TESTING else os.environ.get("THROTTLE_LOGIN", "10/min"),
        "agent": None if TESTING else os.environ.get("THROTTLE_AGENT", "30/min"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AI Sales OS API",
    "DESCRIPTION": "User Level REST API",
    "VERSION": "1.0.0",
}

CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_ALWAYS_EAGER = (
    TESTING or os.environ.get("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
)
CELERY_TASK_EAGER_PROPAGATES = True
CRM_SYNC_INTERVAL_MINUTES = int(os.environ.get("CRM_SYNC_INTERVAL_MINUTES", "60"))
CELERY_BEAT_SCHEDULE = {
    "purge-expired-transcripts": {
        "task": "integrations.purge_expired_transcripts",
        "schedule": crontab(hour=3, minute=0),
    },
    "purge-expired-agent-chats": {
        "task": "ai.purge_expired_agent_chats",
        "schedule": crontab(hour=4, minute=0),
    },
    "sync-all-integration-sources": {
        "task": "integrations.sync_all_sources",
        "schedule": crontab(minute=0),
    },
}

# AI / LLM (OpenRouter-compatible by default)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_CHAT_MODEL = os.environ.get("LLM_CHAT_MODEL", "openai/gpt-4o-mini")
LLM_EMBEDDING_MODEL = os.environ.get("LLM_EMBEDDING_MODEL", "openai/text-embedding-3-small")
LLM_EMBEDDING_DIMENSIONS = int(os.environ.get("LLM_EMBEDDING_DIMENSIONS", "1536"))
AI_CREDENTIALS_KEY = os.environ.get("AI_CREDENTIALS_KEY", SECRET_KEY[:32] if not IS_PRODUCTION else "")

if IS_PRODUCTION and not TESTING and not AI_CREDENTIALS_KEY:
    raise ImproperlyConfigured(
        "AI_CREDENTIALS_KEY environment variable is required in production for encrypted API keys."
    )

TRANSCRIPT_RETENTION_DAYS = int(os.environ.get("TRANSCRIPT_RETENTION_DAYS", "90"))
AGENT_CHAT_RETENTION_DAYS = int(os.environ.get("AGENT_CHAT_RETENTION_DAYS", "90"))

# Speech-to-text (OpenRouter-compatible)
STT_MODEL = os.environ.get("STT_MODEL", "openai/whisper-1")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
DJANGO_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
