from django.conf import settings
from django.core.checks import Error, register
from payments.providers.base import mock_provider_is_allowed


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
    if provider == "ligdicash" and not settings.DEBUG:
        return [
            Error(
                "Production LigdiCash verification is not implemented.",
                hint=(
                    "Keep production payment confirmation disabled until the "
                    "official amount, currency and signature verification "
                    "contract is integrated."
                ),
                id="payments.E004",
            )
        ]
    return []
