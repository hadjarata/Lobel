import hashlib
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape

from orders.models import OrderNotificationReceipt

logger = logging.getLogger(__name__)

EVENT_LABELS = {
    "order_created": "Commande créée",
    "payment_processing": "Paiement en cours de vérification",
    "payment_confirmed": "Paiement confirmé",
    "payment_failed": "Paiement non confirmé",
    "order_preparing": "Commande en préparation",
    "order_shipped": "Commande expédiée",
    "order_delivered": "Commande livrée",
    "order_cancelled": "Commande annulée",
    "order_expired": "Commande expirée",
    "refund_required": "Intervention de remboursement requise",
}


class OrderNotificationService:
    @staticmethod
    def schedule(*, order, event_code):
        recipient = (order.customer_email or "").strip().lower()
        if not recipient or event_code not in EVENT_LABELS:
            return None
        receipt, created = OrderNotificationReceipt.objects.get_or_create(
            order=order,
            event_code=event_code,
            channel="email",
            defaults={
                "recipient_hash": hashlib.sha256(recipient.encode()).hexdigest()
            },
        )
        if created:
            transaction.on_commit(
                lambda receipt_id=receipt.id: OrderNotificationService.dispatch(receipt_id)
            )
        return receipt

    @staticmethod
    def dispatch(receipt_id):
        with transaction.atomic():
            receipt = (
                OrderNotificationReceipt.objects.select_for_update()
                .select_related("order")
                .get(pk=receipt_id)
            )
            if receipt.status == OrderNotificationReceipt.STATUS_SENT:
                return False
            order = receipt.order
            recipient = (order.customer_email or "").strip().lower()
            if not recipient:
                receipt.status = OrderNotificationReceipt.STATUS_FAILED
                receipt.failure_code = "recipient_missing"
                receipt.save(update_fields=["status", "failure_code"])
                return False
            receipt.attempts += 1
            receipt.last_attempt_at = timezone.now()
            receipt.save(update_fields=["attempts", "last_attempt_at"])

        label = EVENT_LABELS[receipt.event_code]
        detail_url = f"{settings.FRONTEND_URL.rstrip('/')}/account/orders/{order.id}"
        subject = f"LobelStore — {label} — commande #{order.id}"
        text = (
            f"{label}\n\nCommande #{order.id}\n"
            f"Montant : {order.total_amount} {order.currency}\n"
            f"Consulter la commande : {detail_url}\n"
        )
        html = (
            f"<h1>{escape(label)}</h1><p>Commande <strong>#{order.id}</strong></p>"
            f"<p>Montant : {escape(str(order.total_amount))} "
            f"{escape(order.currency)}</p><p><a href=\"{escape(detail_url)}\">"
            "Consulter la commande</a></p>"
        )
        try:
            message = EmailMultiAlternatives(
                subject, text, settings.DEFAULT_FROM_EMAIL, [recipient]
            )
            message.attach_alternative(html, "text/html")
            message.send(fail_silently=False)
        except Exception:
            logger.exception(
                "order_notification_failed order_id=%s event=%s receipt_id=%s",
                order.id, receipt.event_code, receipt.id,
            )
            OrderNotificationReceipt.objects.filter(pk=receipt.id).update(
                status=OrderNotificationReceipt.STATUS_FAILED,
                failure_code="delivery_failed",
            )
            return False
        OrderNotificationReceipt.objects.filter(pk=receipt.id).update(
            status=OrderNotificationReceipt.STATUS_SENT,
            sent_at=timezone.now(),
            failure_code="",
        )
        logger.info(
            "order_notification_sent order_id=%s event=%s receipt_id=%s",
            order.id, receipt.event_code, receipt.id,
        )
        return True
