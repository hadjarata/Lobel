from django.conf import settings
from django.core.checks import Error, register
from payments.providers.base import mock_provider_is_allowed
from urllib.parse import urlparse
import ipaddress


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
    signature_required = getattr(
        settings, "PAYMENT_WEBHOOK_SIGNATURE_REQUIRED", False
    )
    if signature_required and provider == "ligdicash":
        from payments.providers.ligdicash import LigdicashProvider
        if not LigdicashProvider.webhook_signature_supported:
            return [Error(
                "LigdiCash webhook signature cannot be required before its "
                "official verification adapter is implemented.",
                id="payments.E008",
            )]
    try:
        for value in getattr(settings, "PAYMENT_WEBHOOK_ALLOWED_IPS", []):
            ipaddress.ip_network(value, strict=False)
    except ValueError:
        return [Error(
            "PAYMENT_WEBHOOK_ALLOWED_IPS contains an invalid IP or CIDR.",
            id="payments.E009",
        )]
    if getattr(settings, "PAYMENT_WEBHOOK_MAX_AGE_SECONDS", 0) <= 0:
        return [Error(
            "PAYMENT_WEBHOOK_MAX_AGE_SECONDS must be positive.",
            id="payments.E010",
        )]
    return []
