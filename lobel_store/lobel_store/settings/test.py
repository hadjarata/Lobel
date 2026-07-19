from .base import *

DEBUG = False
TESTING = True
SETTINGS_ENV = "test"
SECRET_KEY = "test-only-fixed-secret-key-for-lobelstore-tests"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
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
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "tests@lobelstore.invalid"
FRONTEND_URL = "http://testserver"
FRONTEND_RESET_PASSWORD_URL = "http://testserver/reset-password"
FRONTEND_EMAIL_ACTIVATION_URL = "http://testserver/verify-email"
PAYMENT_PROVIDER = "mock"
MEDIA_STORAGE_BACKEND = "local"
MEDIA_LOCAL_STORAGE_IS_PERSISTENT = False
ENABLE_API_DOCS = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}
