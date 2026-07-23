from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from orders.models import Order
from payments.models import Payment
from django.conf import settings


class PaymentProviderError(Exception):
    """Base exception for payment provider failures."""


class PaymentConfigurationError(PaymentProviderError):
    pass


class PaymentCommunicationError(PaymentProviderError):
    pass


class PaymentAPIError(PaymentProviderError):
    pass


class PaymentInvalidResponseError(PaymentProviderError):
    pass


class WebhookParseError(PaymentProviderError):
    pass


def mock_provider_is_allowed() -> bool:
    return bool(settings.DEBUG or getattr(settings, "TESTING", False))


@dataclass(frozen=True)
class CheckoutContext:
    payment: Payment
    order: Order
    amount: int
    currency: str
    order_reference: str
    description: str
    customer_email: str
    customer_firstname: str
    customer_lastname: str
    frontend_url: str = ""


@dataclass(frozen=True)
class CheckoutSessionResult:
    payment_url: str
    session_token: str
    amount: int
    currency: str
    order_reference: str


@dataclass(frozen=True)
class PaymentVerificationResult:
    status: str
    response_code: str
    external_transaction_id: str | None = None
    raw: dict | None = None
    provider: str = ""
    provider_reference: str | None = None
    verified_amount: Decimal | None = None
    verified_currency: str | None = None
    processed_at: datetime | None = None
    signature_verified: bool = False
    verification_implemented: bool = False


@dataclass(frozen=True)
class WebhookAuthenticityResult:
    verified: bool = False
    verification_implemented: bool = False
    method: str = ""
    event_id: str | None = None
    occurred_at: datetime | None = None


@dataclass(frozen=True)
class RefundResult:
    status: str
    response_code: str = ""
    provider_reference: str | None = None
    refunded_amount: Decimal | None = None
    currency: str | None = None
    raw: dict | None = None


@dataclass(frozen=True)
class WebhookResult:
    processed: bool
    message: str


class PaymentProvider(ABC):
    provider_name: str

    @abstractmethod
    def create_checkout(self, context: CheckoutContext) -> CheckoutSessionResult:
        raise NotImplementedError

    @abstractmethod
    def verify_payment(
        self,
        session_token: str,
        *,
        payment: Payment | None = None,
    ) -> PaymentVerificationResult:
        raise NotImplementedError

    def find_payment_by_reference(
        self, merchant_reference: str, *, payment: Payment | None = None
    ) -> PaymentVerificationResult:
        """Recover an ambiguous initialization without creating a new checkout."""
        raise PaymentConfigurationError(
            f"Lookup by merchant reference is not configured for {self.provider_name}."
        )

    @abstractmethod
    def parse_webhook(self, raw_body: bytes, content_type: str | None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def extract_payment_id(self, payload: dict) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def build_deduplication_key(self, payload: dict, payload_hash: str) -> str:
        raise NotImplementedError

    def verify_webhook_authenticity(
        self, raw_body: bytes, headers: dict, payload: dict
    ) -> WebhookAuthenticityResult:
        return WebhookAuthenticityResult()

    def create_refund(self, refund) -> RefundResult:
        raise PaymentConfigurationError(
            f"Refund creation is not configured for provider {self.provider_name}."
        )

    def verify_refund(self, refund) -> RefundResult:
        raise PaymentConfigurationError(
            f"Refund verification is not configured for provider {self.provider_name}."
        )

    @staticmethod
    def format_amount(amount: Decimal) -> int:
        from store.money import xof_integer

        return int(xof_integer(amount))


def validate_provider_confirmation(
    *,
    payment: Payment,
    result: PaymentVerificationResult,
    require_signature: bool,
) -> None:
    """Validate normalized, provider-verified data before business processing."""

    if not result.verification_implemented:
        raise PaymentInvalidResponseError(
            "Payment provider verification is not implemented."
        )
    if result.status != "completed":
        raise PaymentInvalidResponseError(
            f"Payment provider status is not successful: {result.status or 'missing'}."
        )
    if result.verified_amount is None:
        raise PaymentInvalidResponseError("Verified payment amount is missing.")
    if not result.verified_currency:
        raise PaymentInvalidResponseError("Verified payment currency is missing.")
    if not result.provider_reference:
        raise PaymentInvalidResponseError("Verified provider reference is missing.")
    if require_signature and not result.signature_verified:
        raise PaymentInvalidResponseError("Payment webhook signature is not verified.")

    try:
        verified_amount = Decimal(result.verified_amount)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PaymentInvalidResponseError("Verified payment amount is invalid.") from exc

    if verified_amount != payment.amount:
        raise PaymentInvalidResponseError(
            "Verified payment amount does not match the expected amount."
        )
    if result.verified_currency.strip().upper() != payment.currency.strip().upper():
        raise PaymentInvalidResponseError(
            "Verified payment currency does not match the expected currency."
        )
    if result.provider_reference != payment.order_reference:
        raise PaymentInvalidResponseError(
            "Verified provider reference does not match the expected reference."
        )
