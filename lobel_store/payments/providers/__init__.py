from django.conf import settings

from .base import PaymentProvider
from .ligdicash import LigdicashProvider
from .mock import MockProvider


def get_payment_provider() -> PaymentProvider:
    provider_name = getattr(settings, "PAYMENT_PROVIDER", "mock")

    if provider_name == "mock":
        return MockProvider()

    if provider_name == "ligdicash":
        return LigdicashProvider()

    raise ValueError(f"Payment provider not supported: {provider_name}")
