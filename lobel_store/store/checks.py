from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, deploy=True)
def production_configuration_check(app_configs, **kwargs):
    if getattr(settings, "SETTINGS_ENV", "") != "production":
        return []
    rules = [
        (settings.DEBUG is False, "production.E001", "DEBUG must be false."),
        (bool(settings.SECRET_KEY), "production.E002", "SECRET_KEY must be configured."),
        (bool(settings.ALLOWED_HOSTS), "production.E003", "ALLOWED_HOSTS must not be empty."),
        ("*" not in settings.ALLOWED_HOSTS, "production.E004", "Wildcard hosts are forbidden."),
        (not settings.CORS_ALLOW_ALL_ORIGINS, "production.E005", "CORS cannot allow every origin."),
        (bool(settings.CSRF_TRUSTED_ORIGINS), "production.E006", "CSRF trusted origins are required."),
        (settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE, "production.E007", "Secure cookies are required."),
        (settings.SECURE_SSL_REDIRECT, "production.E008", "HTTPS redirect is required."),
        (settings.PAYMENT_PROVIDER != "mock", "production.E009", "Mock payments are forbidden."),
        ("console" not in settings.EMAIL_BACKEND and "locmem" not in settings.EMAIL_BACKEND, "production.E010", "A real email backend is required."),
        (getattr(settings, "MEDIA_LOCAL_STORAGE_IS_PERSISTENT", False), "production.E011", "Persistent media storage is required."),
        (settings.SECURE_HSTS_SECONDS > 0, "production.E013", "HSTS must be positive."),
        (settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql", "production.E014", "PostgreSQL is required."),
    ]
    return [Error(message, id=code) for valid, code, message in rules if not valid]
