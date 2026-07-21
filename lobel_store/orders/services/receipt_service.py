import uuid
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from orders.models import Order, OrderReceipt


ELIGIBLE_RECEIPT_STATUSES = frozenset({
    "paid", "preparing", "shipped", "delivered",
    "refund_required", "refund_pending", "refunded", "refund_failed",
})


def _money(value):
    return f"{Decimal(value or 0):.2f}"


class OrderReceiptService:
    @transaction.atomic
    def issue(self, *, order, payment):
        order = Order.objects.select_for_update().get(pk=order.pk)
        existing = OrderReceipt.objects.select_for_update().filter(
            order=order
        ).first()
        if existing:
            return existing, False
        if (
            order.status not in ELIGIBLE_RECEIPT_STATUSES
            or not order.paid_at
            or not order.snapshot_at
            or payment is None
            or payment.status != "completed"
            or payment.order_id != order.id
            or payment.amount != order.total_amount
            or payment.currency != order.currency
        ):
            raise ValueError("La commande ne possède pas de paiement confirmé.")

        issued_at = order.paid_at
        snapshot = self._snapshot(order=order, payment=payment, issued_at=issued_at)
        pending_number = f"P-{uuid.uuid4().hex[:30]}"
        try:
            with transaction.atomic():
                receipt = OrderReceipt.objects.create(
                    order=order,
                    receipt_number=pending_number,
                    issued_at=issued_at,
                    snapshot=snapshot,
                )
        except IntegrityError:
            return OrderReceipt.objects.get(order=order), False
        number = f"LOBEL-RCPT-{issued_at.year}-{receipt.pk:06d}"
        OrderReceipt.objects.filter(pk=receipt.pk).update(receipt_number=number)
        receipt.refresh_from_db()
        return receipt, True

    def _snapshot(self, *, order, payment, issued_at):
        reference = (
            payment.merchant_reference
            or payment.order_reference
            or order.transaction_id
            or ""
        )
        return {
            "document_title": "Justificatif de commande",
            "order_id": order.id,
            "ordered_at": order.date_ordered.isoformat(),
            "issued_at": issued_at.isoformat(),
            "paid_at": order.paid_at.isoformat(),
            "payment_reference": reference,
            "payment_method": payment.get_payment_method_display(),
            "payment_status": "Payé",
            "currency": order.currency,
            "customer": {
                "name": order.delivery_recipient_name or order.customer_name,
                "email": order.customer_email,
                "phone": order.delivery_phone,
                "address": order.delivery_address,
            },
            "items": [
                {
                    "product": item.product_name or "Produit",
                    "variant": item.variant_name,
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "unit_price": _money(item.unit_price),
                    "line_total": _money(item.subtotal),
                }
                for item in order.items.all().order_by("id")
            ],
            "totals": {
                "subtotal": _money(order.subtotal_amount),
                "discount": _money(order.discount_amount),
                "shipping": _money(order.shipping_amount),
                "total": _money(order.total_amount),
            },
        }
