import json
import logging
import secrets
from decimal import Decimal

from django.conf import settings

from .base import (
    CheckoutContext,
    CheckoutSessionResult,
    PaymentProvider,
    PaymentVerificationResult,
    WebhookParseError,
)

logger = logging.getLogger(__name__)


class MockProvider(PaymentProvider):
    provider_name = "mock"

    def create_checkout(self, context: CheckoutContext) -> CheckoutSessionResult:
        session_token = f"mock_{context.payment.id}_{secrets.token_urlsafe(12)}"
        frontend_url = (context.frontend_url or settings.FRONTEND_URL).rstrip("/")
        payment_url = (
            f"{frontend_url}/checkout/success"
            f"?mock=true&paymentId={context.payment.id}&orderId={context.order.id}"
        )

        logger.info(
            "[Payment] mock checkout created - payment_id=%s order_id=%s",
            context.payment.id,
            context.order.id,
        )

        return CheckoutSessionResult(
            payment_url=payment_url,
            session_token=session_token,
            amount=context.amount,
            currency=context.currency,
            order_reference=context.order_reference,
        )

    def verify_payment(
        self,
        session_token: str,
        *,
        payment=None,
    ) -> PaymentVerificationResult:
        logger.info("[Payment] mock payment verified - token=%s", session_token)

        return PaymentVerificationResult(
            status="completed",
            response_code="00",
            external_transaction_id=f"MOCK-{session_token}",
            provider=self.provider_name,
            provider_reference=payment.order_reference if payment else None,
            verified_amount=Decimal(payment.amount) if payment else None,
            verified_currency=payment.currency if payment else None,
            signature_verified=True,
            verification_implemented=payment is not None,
        )

    def parse_webhook(self, raw_body: bytes, content_type: str | None) -> dict:
        if not raw_body:
            raise WebhookParseError("Empty mock webhook body.")

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise WebhookParseError("Invalid mock webhook JSON.") from exc

        if not isinstance(payload, dict):
            raise WebhookParseError("Invalid mock webhook payload.")

        return payload

    def extract_payment_id(self, payload: dict) -> int | None:
        payment_id = payload.get("paymentId") or payload.get("payment_id")
        if payment_id is None:
            return None

        try:
            return int(payment_id)
        except (TypeError, ValueError):
            return None

    def build_deduplication_key(self, payload: dict, payload_hash: str) -> str:
        payment_id = payload.get("paymentId") or payload.get("payment_id")
        if payment_id is not None:
            return f"mock:payment:{payment_id}"
        return f"mock:hash:{payload_hash}"
