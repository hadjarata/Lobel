import logging

from django.db import transaction

from orders.services.order_service import InsufficientStockError, OrderFulfillmentError
from payments.models import Payment
from payments.providers import get_payment_provider
from payments.providers.base import (
    PaymentConfigurationError,
    PaymentInvalidResponseError,
    mock_provider_is_allowed,
    validate_provider_confirmation,
)
from payments.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class MockConfirmError(Exception):
    pass


class PaymentNotFoundError(MockConfirmError):
    pass


class PaymentAlreadyProcessedError(MockConfirmError):
    pass


class MockConfirmService:
    def __init__(self, payment_service: PaymentService | None = None):
        self.payment_service = payment_service or PaymentService()

    @transaction.atomic
    def confirm_payment(self, *, user, payment_id: int) -> Payment:
        if not mock_provider_is_allowed():
            raise PaymentConfigurationError(
                "Mock payment confirmation is forbidden when DEBUG=False."
            )

        payment = (
            Payment.objects.select_for_update()
            .filter(
                pk=payment_id,
                provider="mock",
                order__customer__user=user,
            )
            .first()
        )

        if payment is None:
            raise PaymentNotFoundError("Paiement introuvable.")

        if payment.processed_at:
            logger.info("[Payment] mock confirm skipped - already processed payment_id=%s", payment.id)
            raise PaymentAlreadyProcessedError("Paiement déjà traité.")

        provider = get_payment_provider()
        if provider.provider_name != "mock":
            raise MockConfirmError("Confirmation mock indisponible pour ce provider.")

        if not payment.session_token:
            raise MockConfirmError("Session de paiement mock invalide.")

        verification = provider.verify_payment(
            payment.session_token,
            payment=payment,
        )
        try:
            validate_provider_confirmation(
                payment=payment,
                result=verification,
                require_signature=False,
            )
        except PaymentInvalidResponseError as exc:
            raise MockConfirmError(str(exc)) from exc

        payment.status = "completed"
        if verification.external_transaction_id:
            payment.external_transaction_id = verification.external_transaction_id
        payment.save(update_fields=["status", "external_transaction_id"])

        self.payment_service.handle_payment_completed(payment)

        logger.info(
            "[Payment] mock payment success - payment_id=%s order_id=%s",
            payment.id,
            payment.order_id,
        )

        payment.refresh_from_db()
        return payment
