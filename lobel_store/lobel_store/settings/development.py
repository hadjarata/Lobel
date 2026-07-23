import os

from .base import *

DEBUG = True
TESTING = False
SETTINGS_ENV = "development"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or os.getenv("SECRET_KEY") or "development-only-key-never-use-in-production"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"] + env.list("ALLOWED_HOSTS", default=[])
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME", default="lobel_store_db"),
        "USER": env("DATABASE_USER", default="postgres"),
        "PASSWORD": env("DATABASE_PASSWORD", default=""),
        "HOST": env("DATABASE_HOST", default="localhost"),
        "PORT": env.int("DATABASE_PORT", default=5433),
    }
}
CORS_ALLOWED_ORIGINS = env.list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
CORS_ALLOW_ALL_ORIGINS = False
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")
FRONTEND_RESET_PASSWORD_URL = env("FRONTEND_RESET_PASSWORD_URL", default="")
FRONTEND_EMAIL_ACTIVATION_URL = env("FRONTEND_EMAIL_ACTIVATION_URL", default="")
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="mock")
LIGDICASH_ENVIRONMENT = env("LIGDICASH_ENVIRONMENT", default="integration")
LIGDICASH_HTTP_TIMEOUT = env.int("LIGDICASH_HTTP_TIMEOUT", default=15)
LIGDICASH_VERIFY_TLS = env.bool("LIGDICASH_VERIFY_TLS", default=True)
LIGDICASH_ALLOWED_CHECKOUT_HOSTS = env.list(
    "LIGDICASH_ALLOWED_CHECKOUT_HOSTS", default=["app.ligdicash.com"]
)
PAYMENT_WEBHOOK_SIGNATURE_REQUIRED = env.bool(
    "PAYMENT_WEBHOOK_SIGNATURE_REQUIRED", default=False
)
PAYMENT_WEBHOOK_ALLOWED_IPS = env.list(
    "PAYMENT_WEBHOOK_ALLOWED_IPS", default=[]
)
PAYMENT_WEBHOOK_MAX_AGE_SECONDS = env.int(
    "PAYMENT_WEBHOOK_MAX_AGE_SECONDS", default=300
)
MEDIA_STORAGE_BACKEND = "local"
MEDIA_LOCAL_STORAGE_IS_PERSISTENT = False
ENABLE_API_DOCS = True
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
