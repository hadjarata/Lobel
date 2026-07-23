import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from orders.models import Order
from orders.services.lifecycle_service import OrderLifecycleService
from orders.services.order_service import OrderFulfillmentError, OrderService
from payments.models import Payment, PaymentOperationalAlert
from payments.services.audit_service import PaymentAuditService


logger = logging.getLogger(__name__)


class PaymentProcessingError(Exception):
    pass


class PaymentService:
    def __init__(self, order_service: OrderService | None = None):
        self.order_service = order_service or OrderService()

    @transaction.atomic
    def handle_payment_completed(self, payment: Payment) -> str:
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.processed_at:
            logger.info(
                "Payment business processing already done - Payment=%s",
                payment.id,
            )
            return payment.status

        logger.info("[Payment] Payment completed received - payment_id=%s", payment.id)

        order = self._resolve_order(payment)
        order = Order.objects.select_for_update().get(pk=order.pk)
        primary_payment = (
            Payment.objects.filter(
                order=order,
                status="completed",
                processed_at__isnull=False,
                failure_code="",
            )
            .exclude(pk=payment.pk)
            .order_by("processed_at", "id")
            .first()
        )
        if primary_payment is not None:
            return self._mark_duplicate_payment(
                payment=payment,
                order=order,
                primary_payment=primary_payment,
            )
        if order.total_amount is not None and Decimal(payment.amount) != order.total_amount:
            raise PaymentProcessingError(
                "Payment amount does not match the frozen order total."
            )
        if order.currency and payment.currency.upper() != order.currency.upper():
            raise PaymentProcessingError(
                "Payment currency does not match the frozen order currency."
            )
        logger.info(
            "Order linked to payment - Payment=%s Order=%s",
            payment.id,
            order.id,
        )

        if order.status in {Order.STATUS_CANCELLED, Order.STATUS_EXPIRED}:
            OrderLifecycleService().transition_order(
                order=order,
                target_status=Order.STATUS_REFUND_REQUIRED,
                actor=None,
                reason_code="late_payment_confirmed",
                source="payment_reconciliation",
                payment=payment,
                metadata={"payment_id": payment.id},
            )
            payment.processed_at = timezone.now()
            payment.failure_code = "late_payment_refund_required"
            payment.save(update_fields=["processed_at", "failure_code"])
            PaymentAuditService.record(
                payment=payment,
                event_type="late_payment",
                from_status=payment.status,
                to_status=payment.status,
                metadata={"order_id": order.id, "refund_required": True},
            )
            logger.error(
                "late_payment_requires_reconciliation payment_id=%s order_id=%s",
                payment.id, order.id,
            )
            return payment.status

        try:
            self.order_service.fulfill_order(order, payment)
        except OrderFulfillmentError as exc:
            order.refresh_from_db()
            if order.status in {
                Order.STATUS_PENDING_PAYMENT,
                Order.STATUS_PAYMENT_PROCESSING,
                Order.STATUS_PAYMENT_FAILED,
                Order.STATUS_CANCELLED,
                Order.STATUS_EXPIRED,
            }:
                OrderLifecycleService().transition_order(
                    order=order,
                    target_status=Order.STATUS_REFUND_REQUIRED,
                    actor=None,
                    reason_code=(
                        "paid_order_unfulfillable"
                        if order.status not in {Order.STATUS_CANCELLED, Order.STATUS_EXPIRED}
                        else "late_payment_confirmed"
                    ),
                    source="payment_reconciliation",
                    payment=payment,
                    metadata={
                        "payment_id": payment.id,
                        "fulfillment_error": type(exc).__name__,
                    },
                )
            else:
                raise
            payment.processed_at = timezone.now()
            payment.failure_code = "payment_refund_required"
            payment.save(update_fields=["processed_at", "failure_code"])
            PaymentAuditService.record(
                payment=payment,
                event_type="fulfillment_failed",
                from_status=payment.status,
                to_status=payment.status,
                metadata={
                    "order_id": order.id,
                    "error_type": type(exc).__name__,
                    "refund_required": True,
                },
            )
            logger.error(
                "paid_order_requires_refund payment_id=%s order_id=%s reason=%s",
                payment.id, order.id, type(exc).__name__,
            )
            return payment.status

        payment.processed_at = timezone.now()
        payment.save(update_fields=["processed_at"])

        logger.info(
            "Payment business processing completed - Payment=%s Order=%s",
            payment.id,
            order.id,
        )
        return payment.status

    @staticmethod
    def _mark_duplicate_payment(*, payment, order, primary_payment):
        now = timezone.now()
        previous_status = payment.status
        payment.status = "refund_required"
        payment.provider_status = payment.provider_status or "completed"
        payment.failure_code = "duplicate_payment"
        payment.failure_message = (
            f"Paiement confirmé après le paiement commercial #{primary_payment.id}."
        )
        payment.processed_at = now
        payment.confirmed_at = payment.confirmed_at or now
        payment.save(update_fields=[
            "status", "provider_status", "failure_code", "failure_message",
            "processed_at", "confirmed_at", "updated_at",
        ])
        PaymentAuditService.record(
            payment=payment,
            event_type="duplicate_payment_detected",
            from_status=previous_status,
            to_status="refund_required",
            metadata={
                "order_id": order.id,
                "primary_payment_id": primary_payment.id,
            },
        )
        PaymentOperationalAlert.objects.get_or_create(
            payment=payment,
            alert_type="duplicate_payment",
            defaults={
                "order": order,
                "severity": "critical",
                "message": (
                    f"Le paiement #{payment.id} est un second encaissement confirmé "
                    f"pour la commande #{order.id}. Remboursement requis."
                ),
                "metadata": {"primary_payment_id": primary_payment.id},
            },
        )
        logger.critical(
            "duplicate_payment_requires_refund payment_id=%s primary_payment_id=%s "
            "order_id=%s",
            payment.id, primary_payment.id, order.id,
        )
        return payment.status

    def _resolve_order(self, payment: Payment) -> Order:
        if payment.merchant_reference:
            if payment.order_reference != payment.merchant_reference:
                raise PaymentProcessingError("Payment merchant reference mismatch.")
            return payment.order
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
