import logging

from django.db import transaction
from django.utils import timezone

from orders.models import Order
from orders.services.order_service import OrderFulfillmentError, OrderService
from payments.models import Payment


logger = logging.getLogger(__name__)


class PaymentProcessingError(Exception):
    pass


class PaymentService:
    def __init__(self, order_service: OrderService | None = None):
        self.order_service = order_service or OrderService()

    @transaction.atomic
    def handle_payment_completed(self, payment: Payment) -> None:
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.processed_at:
            logger.info(
                "Payment business processing already done - Payment=%s",
                payment.id,
            )
            return

        logger.info("[Payment] Payment completed received - payment_id=%s", payment.id)

        order = self._resolve_order(payment)
        logger.info(
            "Order linked to payment - Payment=%s Order=%s",
            payment.id,
            order.id,
        )

        self.order_service.fulfill_order(order, payment)

        payment.processed_at = timezone.now()
        payment.save(update_fields=["processed_at"])

        logger.info(
            "Payment business processing completed - Payment=%s Order=%s",
            payment.id,
            order.id,
        )

    def _resolve_order(self, payment: Payment) -> Order:
        if payment.order_reference:
            expected_order_id = OrderService.parse_order_id_from_reference(
                payment.order_reference
            )
            if expected_order_id is None:
                raise PaymentProcessingError(
                    f"Invalid order reference format: {payment.order_reference}"
                )
            if payment.order_id != expected_order_id:
                raise PaymentProcessingError(
                    f"Payment order mismatch: payment.order_id={payment.order_id}, "
                    f"order_reference={payment.order_reference}"
                )

        return payment.order
