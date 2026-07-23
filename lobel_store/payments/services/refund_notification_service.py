import hashlib
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from payments.models import RefundNotificationReceipt

logger = logging.getLogger(__name__)

LABELS = {
    "refund_requested": "Demande de remboursement enregistrée",
    "refund_processing": "Remboursement en cours",
    "refund_completed": "Remboursement effectué",
    "refund_failed": "Remboursement à vérifier",
}


class RefundNotificationService:
    @staticmethod
    def schedule(*, refund, event_code):
        recipient = (refund.order.customer_email or "").strip().lower()
        if not recipient or event_code not in LABELS:
            return None
        receipt, created = RefundNotificationReceipt.objects.get_or_create(
            refund=refund,
            event_code=event_code,
            defaults={
                "recipient_hash": hashlib.sha256(recipient.encode()).hexdigest()
            },
        )
        if created:
            transaction.on_commit(
                lambda receipt_id=receipt.id: RefundNotificationService.dispatch(
                    receipt_id
                )
            )
        return receipt

    @staticmethod
    def dispatch(receipt_id):
        with transaction.atomic():
            receipt = (
                RefundNotificationReceipt.objects.select_for_update()
                .select_related("refund__order")
                .get(pk=receipt_id)
            )
            if receipt.status == "sent":
                return False
            refund = receipt.refund
            recipient = (refund.order.customer_email or "").strip().lower()
            if not recipient:
                receipt.status = "failed"
                receipt.failure_code = "recipient_missing"
                receipt.save(update_fields=["status", "failure_code"])
                return False
            receipt.attempts += 1
            receipt.last_attempt_at = timezone.now()
            receipt.save(update_fields=["attempts", "last_attempt_at"])

        label = LABELS[receipt.event_code]
        subject = f"LobelStore — {label} — commande #{refund.order_id}"
        body = (
            f"{label}\n\nCommande #{refund.order_id}\n"
            f"Montant : {refund.amount} {refund.currency}\n"
            f"Référence : {refund.uuid}\n"
        )
        try:
            EmailMultiAlternatives(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
            ).send(fail_silently=False)
        except Exception:
            logger.exception(
                "refund_notification_failed refund_id=%s event=%s",
                refund.id,
                receipt.event_code,
            )
            RefundNotificationReceipt.objects.filter(pk=receipt.id).update(
                status="failed",
                failure_code="delivery_failed",
            )
            return False
        RefundNotificationReceipt.objects.filter(pk=receipt.id).update(
            status="sent",
            sent_at=timezone.now(),
            failure_code="",
        )
        return True
