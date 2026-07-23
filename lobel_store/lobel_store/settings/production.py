from urllib.parse import urlparse

from corsheaders.defaults import default_headers, default_methods
from django.core.exceptions import ImproperlyConfigured

from .base import *
from .env import (
    env_bool, env_https_url, env_https_url_list, env_int,
    env_list_required, env_optional, env_required,
)

DEBUG = False
TESTING = False
SETTINGS_ENV = "production"

SECRET_KEY = env_required("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50 or any(marker in SECRET_KEY.lower() for marker in ("django-insecure", "changeme", "development", "test-secret")):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is too short or uses a forbidden example value.")

ALLOWED_HOSTS = env_list_required("DJANGO_ALLOWED_HOSTS")
if any(host == "*" or "://" in host or "/" in host or host in {"localhost", "127.0.0.1"} for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS contains a forbidden production host.")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_required("DATABASE_NAME"),
        "USER": env_required("DATABASE_USER"),
        "PASSWORD": env_required("DATABASE_PASSWORD"),
        "HOST": env_required("DATABASE_HOST"),
        "PORT": env_int("DATABASE_PORT", minimum=1),
        "CONN_MAX_AGE": env_int("DATABASE_CONN_MAX_AGE", default=60, minimum=0),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"sslmode": env_optional("DATABASE_SSLMODE", "require")},
    }
}
if DATABASES["default"]["OPTIONS"]["sslmode"] not in {"require", "verify-ca", "verify-full"}:
    raise ImproperlyConfigured("DATABASE_SSLMODE must require TLS in production.")

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env_https_url_list("DJANGO_CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = env_bool("DJANGO_CORS_ALLOW_CREDENTIALS", default=False)
CORS_ALLOW_HEADERS = tuple(default_headers)
CORS_ALLOW_METHODS = tuple(default_methods)
CSRF_TRUSTED_ORIGINS = env_https_url_list("DJANGO_CSRF_TRUSTED_ORIGINS")

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", default=True)
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", minimum=1)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
if SECURE_HSTS_PRELOAD and (SECURE_HSTS_SECONDS < 31_536_000 or not SECURE_HSTS_INCLUDE_SUBDOMAINS):
    raise ImproperlyConfigured("HSTS preload requires one year and includeSubDomains.")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env_required("EMAIL_HOST")
EMAIL_PORT = env_int("EMAIL_PORT", minimum=1)
EMAIL_HOST_USER = env_required("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env_required("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", default=False)
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.")
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", default=10, minimum=1)
DEFAULT_FROM_EMAIL = env_required("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = env_required("SERVER_EMAIL")

FRONTEND_URL = env_https_url("FRONTEND_BASE_URL")
FRONTEND_RESET_PASSWORD_URL = env_https_url("PASSWORD_RESET_FRONTEND_URL")
FRONTEND_EMAIL_ACTIVATION_URL = env_https_url("EMAIL_VERIFICATION_FRONTEND_URL")

PAYMENT_PROVIDER = env_required("PAYMENT_PROVIDER").lower()
if PAYMENT_PROVIDER != "ligdicash":
    raise ImproperlyConfigured("Production requires the configured real LigdiCash provider.")
LIGDICASH_API_KEY = env_required("LIGDICASH_API_KEY")
LIGDICASH_API_TOKEN = env_required("LIGDICASH_API_TOKEN")
LIGDICASH_BASE_URL = env_https_url("LIGDICASH_BASE_URL")
if urlparse(LIGDICASH_BASE_URL).hostname != "app.ligdicash.com":
    raise ImproperlyConfigured(
        "LIGDICASH_BASE_URL must target app.ligdicash.com in production."
    )
LIGDICASH_STORE_NAME = env_required("LIGDICASH_STORE_NAME")
LIGDICASH_STORE_URL = env_https_url("LIGDICASH_STORE_URL")
LIGDICASH_RETURN_URL = env_https_url("LIGDICASH_RETURN_URL")
LIGDICASH_CANCEL_URL = env_https_url("LIGDICASH_CANCEL_URL")
LIGDICASH_CALLBACK_URL = env_https_url("LIGDICASH_CALLBACK_URL")
LIGDICASH_ENVIRONMENT = env_required("LIGDICASH_ENVIRONMENT").lower()
if LIGDICASH_ENVIRONMENT != "production":
    raise ImproperlyConfigured("Production requires LIGDICASH_ENVIRONMENT=production.")
LIGDICASH_HTTP_TIMEOUT = env_int("LIGDICASH_HTTP_TIMEOUT", minimum=1)
LIGDICASH_VERIFY_TLS = env_bool("LIGDICASH_VERIFY_TLS")
if not LIGDICASH_VERIFY_TLS:
    raise ImproperlyConfigured("LigdiCash TLS verification cannot be disabled.")
LIGDICASH_ALLOWED_CHECKOUT_HOSTS = env_list_required("LIGDICASH_ALLOWED_CHECKOUT_HOSTS")
if "app.ligdicash.com" not in LIGDICASH_ALLOWED_CHECKOUT_HOSTS:
    raise ImproperlyConfigured("The official LigdiCash checkout host must be allowed.")
PAYMENT_WEBHOOK_SIGNATURE_REQUIRED = env_bool(
    "PAYMENT_WEBHOOK_SIGNATURE_REQUIRED", default=False
)
PAYMENT_WEBHOOK_ALLOWED_IPS = env.list(
    "PAYMENT_WEBHOOK_ALLOWED_IPS", default=[]
)
PAYMENT_WEBHOOK_MAX_AGE_SECONDS = env_int(
    "PAYMENT_WEBHOOK_MAX_AGE_SECONDS", default=300, minimum=1
)

MEDIA_STORAGE_BACKEND = env_required("MEDIA_STORAGE_BACKEND").lower()
MEDIA_LOCAL_STORAGE_IS_PERSISTENT = env_bool("MEDIA_LOCAL_STORAGE_IS_PERSISTENT")
if MEDIA_STORAGE_BACKEND != "local" or not MEDIA_LOCAL_STORAGE_IS_PERSISTENT:
    raise ImproperlyConfigured("A confirmed persistent local media volume is required by the installed storage backend.")
MEDIA_ROOT = env_required("MEDIA_PERSISTENT_ROOT")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}

ENABLE_API_DOCS = env_bool("ENABLE_API_DOCS", default=False)
ADMIN_PATH = env_optional("DJANGO_ADMIN_PATH", "admin/").strip("/")
if not ADMIN_PATH or "/" in ADMIN_PATH:
    raise ImproperlyConfigured("DJANGO_ADMIN_PATH must be one safe path segment.")

LOG_LEVEL = env_required("DJANGO_LOG_LEVEL").upper()
if LOG_LEVEL not in {"INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ImproperlyConfigured("DJANGO_LOG_LEVEL is invalid for production.")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}
