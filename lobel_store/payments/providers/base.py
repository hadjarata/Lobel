from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from orders.models import Order
from payments.models import Payment


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
    def verify_payment(self, session_token: str) -> PaymentVerificationResult:
        raise NotImplementedError

    @abstractmethod
    def parse_webhook(self, raw_body: bytes, content_type: str | None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def extract_payment_id(self, payload: dict) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def build_deduplication_key(self, payload: dict, payload_hash: str) -> str:
        raise NotImplementedError

    @staticmethod
    def format_amount(amount: Decimal) -> int:
        from decimal import ROUND_HALF_UP

        return int(Decimal(amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
