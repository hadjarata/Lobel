from django.conf import settings

from .base import (
    PaymentConfigurationError,
    PaymentProvider,
    mock_provider_is_allowed,
)
from .ligdicash import LigdicashProvider
from .mock import MockProvider


def get_payment_provider() -> PaymentProvider:
    provider_name = str(getattr(settings, "PAYMENT_PROVIDER", "") or "").strip().lower()

    if not provider_name:
        raise PaymentConfigurationError(
            "PAYMENT_PROVIDER must be configured explicitly."
        )

    if provider_name == "mock":
        if not mock_provider_is_allowed():
            raise PaymentConfigurationError(
                "The mock payment provider is forbidden when DEBUG=False."
            )
        return MockProvider()

    if provider_name == "ligdicash":
        return LigdicashProvider()

    raise PaymentConfigurationError(
        f"Payment provider not supported: {provider_name}"
    )
