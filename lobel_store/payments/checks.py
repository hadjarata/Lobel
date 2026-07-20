from django.conf import settings
from django.core.checks import Error, register
from payments.providers.base import mock_provider_is_allowed
from urllib.parse import urlparse


SUPPORTED_PROVIDERS = {"mock", "ligdicash"}


@register()
def payment_configuration_check(app_configs, **kwargs):
    provider = str(getattr(settings, "PAYMENT_PROVIDER", "") or "").strip().lower()

    if not provider:
        return [
            Error(
                "PAYMENT_PROVIDER must be configured explicitly.",
                id="payments.E001",
            )
        ]
    if provider not in SUPPORTED_PROVIDERS:
        return [
            Error(
                f"Unsupported PAYMENT_PROVIDER: {provider}",
                id="payments.E002",
            )
        ]
    if provider == "mock" and not mock_provider_is_allowed():
        return [
            Error(
                "The mock payment provider is forbidden when DEBUG=False.",
                id="payments.E003",
            )
        ]
    if provider == "ligdicash":
        required = [
            "LIGDICASH_API_KEY", "LIGDICASH_API_TOKEN", "LIGDICASH_BASE_URL",
            "LIGDICASH_RETURN_URL", "LIGDICASH_CANCEL_URL",
            "LIGDICASH_CALLBACK_URL",
        ]
        missing = [name for name in required if not getattr(settings, name, "")]
        if missing:
            return [Error(
                "Required LigdiCash configuration is missing.",
                hint=", ".join(missing), id="payments.E004",
            )]
        if getattr(settings, "LIGDICASH_HTTP_TIMEOUT", 0) <= 0:
            return [Error("LigdiCash timeout must be positive.", id="payments.E005")]
        if not getattr(settings, "LIGDICASH_VERIFY_TLS", False):
            return [Error("LigdiCash TLS verification is required.", id="payments.E006")]
        if not settings.DEBUG:
            urls = [
                settings.LIGDICASH_BASE_URL, settings.LIGDICASH_RETURN_URL,
                settings.LIGDICASH_CANCEL_URL, settings.LIGDICASH_CALLBACK_URL,
            ]
            if any(
                urlparse(value).scheme != "https"
                or urlparse(value).hostname in {"localhost", "127.0.0.1"}
                for value in urls
            ):
                return [Error("LigdiCash production URLs must be public HTTPS.", id="payments.E007")]
    return []
