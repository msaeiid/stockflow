"""
Django settings for the StockFlow project.

Every deployment-specific value comes from the environment (or a local ``.env``
file in development). Set ``DJANGO_PRODUCTION=True`` behind a TLS-terminating
proxy: it requires a real ``SECRET_KEY`` and turns on the secure cookie and
proxy settings. See README "Demo deployment".
"""

import os
import re
from datetime import timedelta
from pathlib import Path

import dj_database_url
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# --- Core / security ---------------------------------------------------------

DEBUG = env_bool("DEBUG", False)
PRODUCTION = env_bool("DJANGO_PRODUCTION", False)

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if PRODUCTION:
        raise ImproperlyConfigured("SECRET_KEY must be set when DJANGO_PRODUCTION=True.")
    # Development and tests only; never used when DJANGO_PRODUCTION=True.
    SECRET_KEY = "django-insecure-dev-only-not-for-production"  # noqa: S105
elif PRODUCTION and len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("SECRET_KEY must be at least 50 characters in production.")

if PRODUCTION and DEBUG:
    raise ImproperlyConfigured("DEBUG must be off when DJANGO_PRODUCTION=True.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

if PRODUCTION:
    # TLS is terminated by the reverse proxy, which sets X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    # The proxy redirects HTTP to HTTPS and sets HSTS; doing it here as well would
    # also redirect the container's own healthcheck.
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
    SILENCED_SYSTEM_CHECKS = ["security.W004", "security.W008"]

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# --- Applications ------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "inventory",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"


# --- Database ----------------------------------------------------------------
# DATABASE_URL wins; otherwise POSTGRES_HOST + POSTGRES_* (as in compose.demo.yml,
# so the password lives only once in .env.demo); otherwise a local SQLite file.

if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(conn_max_age=600, conn_health_checks=True),
    }
elif os.getenv("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "stockflow"),
            "USER": os.getenv("POSTGRES_USER", "stockflow"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --- Static files and the built frontend -------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# When the React build (frontend/dist) is present, Django serves it from the same
# origin: WhiteNoise serves its files at the site root and config.urls returns
# index.html for client-side routes.
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", BASE_DIR.parent / "frontend" / "dist"))
if FRONTEND_DIST.is_dir():
    WHITENOISE_ROOT = FRONTEND_DIST

_VITE_HASHED = re.compile(r"^/assets/.+-[A-Za-z0-9_-]{8,}\.[a-z0-9]+$")


def _immutable_file_test(path: str, url: str) -> bool:
    """Vite's hashed bundles and Django's manifest files can be cached forever."""
    return bool(_VITE_HASHED.match(url)) or bool(re.search(r"\.[0-9a-f]{12}\.\w+$", url))


WHITENOISE_IMMUTABLE_FILE_TEST = _immutable_file_test

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Django REST Framework ---------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("THROTTLE_ANON", "20/min"),
        "user": os.getenv("THROTTLE_USER", "120/min"),
    },
    "EXCEPTION_HANDLER": "inventory.exceptions.exception_handler",
}
if os.getenv("DRF_NUM_PROXIES"):
    # Behind N reverse proxies: take the client address from X-Forwarded-For
    # for throttling instead of the proxy's address.
    REST_FRAMEWORK["NUM_PROXIES"] = int(os.environ["DRF_NUM_PROXIES"])

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "StockFlow API",
    "DESCRIPTION": "Inventory and order management system — REST API.",
    "VERSION": "1.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Swagger UI / ReDoc assets are served locally instead of from a CDN.
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}

# Only needed when the frontend runs on another origin (Vite dev server, Vercel).
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "" if PRODUCTION else "http://localhost:5173,http://127.0.0.1:5173",
)


# --- E-mail ------------------------------------------------------------------
# Console backend by default: nothing leaves the server.

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "alerts@stockflow.example.com")
LOW_STOCK_ALERT_EMAIL = os.getenv("LOW_STOCK_ALERT_EMAIL", "manager@stockflow.example.com")


# --- Demo mode ---------------------------------------------------------------
# DEMO_MODE enables the demo_seed / demo_reset commands. DEMO_SHOW_CREDENTIALS
# lets the login page display the shared demo login.

DEMO_MODE = env_bool("DEMO_MODE", False)
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")
DEMO_SHOW_CREDENTIALS = env_bool("DEMO_SHOW_CREDENTIALS", False)


# --- Cache and Celery --------------------------------------------------------

CELERY_BEAT_SCHEDULE = {
    "daily-stock-report": {
        "task": "inventory.tasks.generate_daily_stock_report",
        "schedule": crontab(hour=8, minute=0),
    },
}

REDIS_URL = os.getenv("REDIS_URL", "")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER = False
else:
    # No Redis (demo, free tier, tests): in-memory cache and inline tasks.
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    CELERY_BROKER_URL = "memory://"
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
    "loggers": {
        # Requests for other host names (scanners) are answered 400; no traceback.
        "django.security.DisallowedHost": {"handlers": [], "propagate": False},
    },
}
