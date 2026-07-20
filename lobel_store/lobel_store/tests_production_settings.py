import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    project_dir = Path(__file__).resolve().parent.parent

    def valid_environment(self):
        return {
            "DJANGO_SETTINGS_MODULE": "lobel_store.settings.production",
            "DJANGO_SECRET_KEY": "ci-only-6x!A9q#V2p$R8m-Z4t-W7y-K3n-F5s-J1d-H9u-B6e",
            "DJANGO_ALLOWED_HOSTS": "api.example.com",
            "DATABASE_NAME": "ci_database",
            "DATABASE_USER": "ci_user",
            "DATABASE_PASSWORD": "ci-placeholder-password",
            "DATABASE_HOST": "db.example.internal",
            "DATABASE_PORT": "5432",
            "DATABASE_SSLMODE": "require",
            "DJANGO_CORS_ALLOWED_ORIGINS": "https://shop.example.com",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://shop.example.com",
            "DJANGO_SECURE_HSTS_SECONDS": "31536000",
            "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS": "true",
            "DJANGO_SECURE_HSTS_PRELOAD": "false",
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_PORT": "587",
            "EMAIL_HOST_USER": "ci-user",
            "EMAIL_HOST_PASSWORD": "ci-placeholder-password",
            "EMAIL_USE_TLS": "true",
            "EMAIL_USE_SSL": "false",
            "DEFAULT_FROM_EMAIL": "noreply@example.com",
            "SERVER_EMAIL": "errors@example.com",
            "FRONTEND_BASE_URL": "https://shop.example.com",
            "PASSWORD_RESET_FRONTEND_URL": "https://shop.example.com/reset-password",
            "EMAIL_VERIFICATION_FRONTEND_URL": "https://shop.example.com/verify-email",
            "PAYMENT_PROVIDER": "ligdicash",
            "LIGDICASH_API_KEY": "ci-placeholder",
            "LIGDICASH_API_TOKEN": "ci-placeholder",
            "LIGDICASH_BASE_URL": "https://app.ligdicash.com",
            "LIGDICASH_STORE_NAME": "CI Store",
            "LIGDICASH_STORE_URL": "https://shop.example.com",
            "LIGDICASH_RETURN_URL": "https://shop.example.com/payment/return",
            "LIGDICASH_CANCEL_URL": "https://shop.example.com/payment/cancel",
            "LIGDICASH_CALLBACK_URL": "https://api.example.com/payment/callback",
            "LIGDICASH_ENVIRONMENT": "production",
            "LIGDICASH_HTTP_TIMEOUT": "15",
            "LIGDICASH_VERIFY_TLS": "true",
            "LIGDICASH_ALLOWED_CHECKOUT_HOSTS": "app.ligdicash.com",
            "MEDIA_STORAGE_BACKEND": "local",
            "MEDIA_LOCAL_STORAGE_IS_PERSISTENT": "true",
            "MEDIA_PERSISTENT_ROOT": str(self.project_dir / "test-persistent-media"),
            "DJANGO_LOG_LEVEL": "INFO",
            "ENABLE_API_DOCS": "false",
        }

    def load(self, changes=None):
        environment = os.environ.copy()
        environment.update(self.valid_environment())
        environment.update(changes or {})
        result = subprocess.run(
            [
                sys.executable, "-c",
                (
                    "import json; import django; django.setup(); "
                    "from django.conf import settings; "
                    "print(json.dumps({'DEBUG':settings.DEBUG,"
                    "'SSL':settings.SECURE_SSL_REDIRECT,"
                    "'SESSION':settings.SESSION_COOKIE_SECURE,"
                    "'CSRF':settings.CSRF_COOKIE_SECURE,"
                    "'HSTS':settings.SECURE_HSTS_SECONDS,"
                    "'PAYMENT':settings.PAYMENT_PROVIDER}))"
                ),
            ],
            cwd=self.project_dir,
            env=environment,
            capture_output=True,
            text=True,
        )
        return result

    def test_valid_production_settings_are_secure(self):
        result = self.load()
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(values, {
            "DEBUG": False, "SSL": True, "SESSION": True, "CSRF": True,
            "HSTS": 31536000, "PAYMENT": "ligdicash",
        })

    def test_critical_missing_or_unsafe_values_fail_closed(self):
        cases = {
            "secret absent": {"DJANGO_SECRET_KEY": ""},
            "example secret": {"DJANGO_SECRET_KEY": "django-insecure-" + "x" * 60},
            "database password absent": {"DATABASE_PASSWORD": ""},
            "hosts absent": {"DJANGO_ALLOWED_HOSTS": ""},
            "wildcard host": {"DJANGO_ALLOWED_HOSTS": "*"},
            "wildcard cors": {"DJANGO_CORS_ALLOWED_ORIGINS": "https://*"},
            "csrf absent": {"DJANGO_CSRF_TRUSTED_ORIGINS": ""},
            "mock provider": {"PAYMENT_PROVIDER": "mock"},
            "provider secret absent": {"LIGDICASH_API_TOKEN": ""},
            "integration account in production": {"LIGDICASH_ENVIRONMENT": "integration"},
            "provider TLS disabled": {"LIGDICASH_VERIFY_TLS": "false"},
            "provider timeout invalid": {"LIGDICASH_HTTP_TIMEOUT": "0"},
            "ephemeral media": {"MEDIA_LOCAL_STORAGE_IS_PERSISTENT": "false"},
            "negative hsts": {"DJANGO_SECURE_HSTS_SECONDS": "-1"},
            "http frontend": {"FRONTEND_BASE_URL": "http://shop.example.com"},
            "localhost frontend": {"FRONTEND_BASE_URL": "https://localhost"},
            "invalid log level": {"DJANGO_LOG_LEVEL": "DEBUG"},
        }
        for label, change in cases.items():
            with self.subTest(label=label):
                result = self.load(change)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("ImproperlyConfigured", result.stderr)

    def test_environment_modules_import_independently(self):
        for module in (
            "lobel_store.settings.base",
            "lobel_store.settings.development",
            "lobel_store.settings.test",
        ):
            environment = os.environ.copy()
            environment["DJANGO_SETTINGS_MODULE"] = module
            result = subprocess.run(
                [
                    sys.executable, "-c",
                    (
                        f"import importlib; importlib.import_module('{module}')"
                        if module.endswith(".base")
                        else "import django; django.setup()"
                    ),
                ],
                cwd=self.project_dir, env=environment, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, f"{module}: {result.stderr}")
