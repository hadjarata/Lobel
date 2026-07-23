from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from orders.models import Order, OrderStatusHistory
from orders.services.notification_service import OrderNotificationService
from products.models import Product, ProductVariant


class OrderTransitionError(Exception):
    code = "invalid_order_transition"

    def __init__(self, message, code=None):
        super().__init__(message)
        if code:
            self.code = code


ALLOWED_ORDER_TRANSITIONS = {
    Order.STATUS_CART: {
        Order.STATUS_PENDING_PAYMENT, Order.STATUS_PAID, Order.STATUS_CANCELLED,
    },
    Order.STATUS_PENDING_PAYMENT: {
        Order.STATUS_PAYMENT_PROCESSING, Order.STATUS_PAID,
        Order.STATUS_PAYMENT_FAILED, Order.STATUS_CANCELLED, Order.STATUS_EXPIRED,
        Order.STATUS_REFUND_REQUIRED,
    },
    Order.STATUS_PAYMENT_PROCESSING: {
        Order.STATUS_PAID, Order.STATUS_PAYMENT_FAILED,
        Order.STATUS_CANCELLED, Order.STATUS_EXPIRED,
        Order.STATUS_REFUND_REQUIRED,
    },
    Order.STATUS_PAYMENT_FAILED: {
        Order.STATUS_PAYMENT_PROCESSING, Order.STATUS_CANCELLED,
        Order.STATUS_EXPIRED, Order.STATUS_REFUND_REQUIRED,
    },
    Order.STATUS_PAID: {Order.STATUS_PREPARING, Order.STATUS_REFUND_PENDING},
    Order.STATUS_PREPARING: {
        Order.STATUS_SHIPPED, Order.STATUS_REFUND_PENDING,
    },
    Order.STATUS_SHIPPED: {Order.STATUS_DELIVERED, Order.STATUS_REFUND_PENDING},
    Order.STATUS_DELIVERED: {Order.STATUS_REFUND_PENDING},
    Order.STATUS_CANCELLED: {Order.STATUS_REFUND_REQUIRED},
    Order.STATUS_EXPIRED: {Order.STATUS_REFUND_REQUIRED},
    Order.STATUS_REFUND_REQUIRED: {Order.STATUS_REFUND_PENDING},
    Order.STATUS_REFUND_PENDING: {Order.STATUS_REFUNDED, Order.STATUS_REFUND_FAILED},
    Order.STATUS_REFUND_FAILED: {Order.STATUS_REFUND_PENDING},
}

CANCELLATION_REASONS = frozenset({
    "customer_request", "payment_expired", "out_of_stock", "fraud_suspected",
    "operational_issue", "administrative_correction",
})


class OrderLifecycleService:
    @transaction.atomic
    def transition_order(
        self, *, order, target_status, actor=None, reason_code="",
        reason_note="", metadata=None, payment=None, refund_confirmed=False,
        source="service", correlation_id="",
    ):
        order = Order.objects.select_for_update().get(pk=order.pk)
        current = order.status
        if current == target_status:
            return order, False
        if target_status not in ALLOWED_ORDER_TRANSITIONS.get(current, set()):
            raise OrderTransitionError(
                f"Transition {current} -> {target_status} interdite."
            )
        self._authorize(order=order, current=current, target=target_status, actor=actor)
        self._validate(
            order=order, target=target_status, reason_code=reason_code,
            payment=payment, refund_confirmed=refund_confirmed,
        )
        now = timezone.now()
        update_fields = ["status"]

        if target_status == Order.STATUS_PENDING_PAYMENT:
            self._reserve_stock(order)
            order.stock_reserved_at = now
            order.stock_reservation_expires_at = now + timedelta(
                minutes=settings.ORDER_PENDING_PAYMENT_TTL_MINUTES
            )
            order.stock_released_at = None
            update_fields += [
                "stock_reserved_at", "stock_reservation_expires_at",
                "stock_released_at",
            ]
        elif target_status == Order.STATUS_PAYMENT_PROCESSING:
            order.payment_processing_at = order.payment_processing_at or now
            update_fields.append("payment_processing_at")
        elif target_status == Order.STATUS_PAYMENT_FAILED:
            order.payment_failed_at = order.payment_failed_at or now
            update_fields.append("payment_failed_at")
        elif target_status == Order.STATUS_PAID:
            self._commit_or_consume_stock(order)
            order.stock_consumed_at = now
            order.paid_at = order.paid_at or now
            order.complete = True
            update_fields += ["stock_consumed_at", "paid_at", "complete"]
            if payment and payment.external_transaction_id:
                order.transaction_id = payment.external_transaction_id[:100]
                update_fields.append("transaction_id")
        elif target_status == Order.STATUS_PREPARING:
            order.preparation_started_at = order.preparation_started_at or now
            update_fields.append("preparation_started_at")
        elif target_status == Order.STATUS_SHIPPED:
            order.shipped_at = order.shipped_at or now
            update_fields.append("shipped_at")
        elif target_status == Order.STATUS_DELIVERED:
            order.delivered_at = order.delivered_at or now
            update_fields.append("delivered_at")
        elif target_status == Order.STATUS_CANCELLED:
            if self._release_reserved_stock(order):
                order.stock_released_at = now
                update_fields.append("stock_released_at")
            order.cancelled_at = order.cancelled_at or now
            order.complete = True
            update_fields += ["cancelled_at", "complete"]
        elif target_status == Order.STATUS_EXPIRED:
            if self._release_reserved_stock(order):
                order.stock_released_at = now
                update_fields.append("stock_released_at")
            order.expired_at = order.expired_at or now
            order.complete = True
            update_fields += ["expired_at", "complete"]
        elif target_status == Order.STATUS_REFUND_PENDING:
            order.refund_requested_at = order.refund_requested_at or now
            update_fields.append("refund_requested_at")
        elif target_status == Order.STATUS_REFUNDED:
            order.refunded_at = order.refunded_at or now
            update_fields.append("refunded_at")

        order._apply_status_transition(target_status)
        order.save(update_fields=list(dict.fromkeys(update_fields)))
        if (
            target_status == Order.STATUS_PAID
            and order.snapshot_at
            and order.total_amount is not None
        ):
            from orders.services.receipt_service import OrderReceiptService
            OrderReceiptService().issue(order=order, payment=payment)
        OrderStatusHistory.objects.create(
            order=order, from_status=current, to_status=target_status,
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            actor_role_snapshot=self._actor_role(actor),
            reason_code=reason_code, reason_note=(reason_note or "").strip(),
            source=source[:50], correlation_id=correlation_id[:64],
            metadata=metadata or {},
        )
        event_code = {
            Order.STATUS_PENDING_PAYMENT: "order_created",
            Order.STATUS_PAYMENT_PROCESSING: "payment_processing",
            Order.STATUS_PAID: "payment_confirmed",
            Order.STATUS_PAYMENT_FAILED: "payment_failed",
            Order.STATUS_PREPARING: "order_preparing",
            Order.STATUS_SHIPPED: "order_shipped",
            Order.STATUS_DELIVERED: "order_delivered",
            Order.STATUS_CANCELLED: "order_cancelled",
            Order.STATUS_EXPIRED: "order_expired",
            Order.STATUS_REFUND_REQUIRED: "refund_required",
        }.get(target_status)
        if event_code:
            OrderNotificationService.schedule(order=order, event_code=event_code)
        return order, True

    def _authorize(self, *, order, current, target, actor):
        if actor is None:
            return
        is_staff = bool(actor.is_staff or actor.is_superuser)
        is_owner = bool(order.customer_id and order.customer.user_id == actor.id)
        staff_only = {
            Order.STATUS_PREPARING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED,
            Order.STATUS_REFUND_FAILED, Order.STATUS_REFUNDED,
            Order.STATUS_REFUND_REQUIRED,
        }
        if target in staff_only and not is_staff:
            raise OrderTransitionError("Action réservée au personnel.", "forbidden")
        if target == Order.STATUS_CANCELLED:
            if is_staff:
                return
            cancellable = {
                Order.STATUS_CART, Order.STATUS_PENDING_PAYMENT,
                Order.STATUS_PAYMENT_PROCESSING, Order.STATUS_PAYMENT_FAILED,
            }
            if not is_owner or current not in cancellable:
                raise OrderTransitionError(
                    "Commande non annulable.", "order_not_cancellable"
                )
        elif target == Order.STATUS_REFUND_PENDING:
            if not (is_staff or is_owner):
                raise OrderTransitionError("Remboursement interdit.", "refund_not_allowed")
        elif not is_staff and not is_owner:
            raise OrderTransitionError("Action interdite.", "forbidden")

    def _validate(self, *, order, target, reason_code, payment, refund_confirmed):
        if target == Order.STATUS_PENDING_PAYMENT:
            if not order.snapshot_at or order.total_amount is None or not order.currency:
                raise OrderTransitionError("Snapshots de checkout incomplets.")
            if not order.items.exists():
                raise OrderTransitionError("Commande vide.")
        elif target == Order.STATUS_PAID:
            if payment is None or payment.order_id != order.id or payment.status != "completed":
                raise OrderTransitionError("Paiement non vérifié.", "payment_not_verified")
            if (
                (order.total_amount is not None and payment.amount != order.total_amount)
                or payment.currency != order.currency
            ):
                raise OrderTransitionError(
                    "Montant ou devise incohérent.", "payment_not_verified"
                )
            if order.stock_consumed_at:
                raise OrderTransitionError("Stock déjà consommé.")
        elif target in {
            Order.STATUS_PAYMENT_PROCESSING, Order.STATUS_PAYMENT_FAILED,
        }:
            if payment is None or payment.order_id != order.id:
                raise OrderTransitionError("Paiement incohérent.", "payment_not_verified")
        elif target == Order.STATUS_PREPARING and not order.stock_consumed_at:
            raise OrderTransitionError("Stock non consommé.", "stock_not_consumed")
        elif target == Order.STATUS_CANCELLED:
            if reason_code not in CANCELLATION_REASONS:
                raise OrderTransitionError("Motif d'annulation obligatoire.")
            if order.stock_consumed_at:
                raise OrderTransitionError(
                    "Une commande payée nécessite un remboursement.", "refund_required"
                )
        elif target == Order.STATUS_EXPIRED:
            if order.stock_consumed_at or order.paid_at or (
                payment is not None and payment.status == "completed"
            ):
                raise OrderTransitionError("Une commande payée ne peut pas expirer.")
        elif target == Order.STATUS_REFUND_PENDING:
            if not order.stock_consumed_at and (
                payment is None
                or payment.order_id != order.id
                or payment.status not in {"completed", "refund_required"}
            ):
                raise OrderTransitionError(
                    "Paiement remboursable introuvable.", "order_not_paid"
                )
        elif target == Order.STATUS_REFUNDED and not refund_confirmed:
            raise OrderTransitionError(
                "Une confirmation technique est obligatoire.", "refund_not_allowed"
            )

    def _consume_stock(self, order):
        items, variants = self._locked_items_and_variants(order)
        for item in items:
            variant = variants[item.variant_id]
            if variant.product_id != item.product_id:
                raise OrderTransitionError("Variante incohérente.")
            if not variant.product.is_active or not variant.is_active:
                raise OrderTransitionError("Produit ou variante inactif.")
            if variant.stock < item.quantity:
                raise OrderTransitionError(
                    f"Stock insuffisant pour la variante {variant.id}.",
                    "insufficient_stock",
                )
            ProductVariant.objects.filter(pk=variant.pk).update(
                stock=F("stock") - item.quantity
            )
            Product.objects.filter(pk=variant.product_id).update(
                sales_count=F("sales_count") + item.quantity
            )

    def _reserve_stock(self, order):
        items, variants = self._locked_items_and_variants(order)
        for item in items:
            variant = variants[item.variant_id]
            if variant.product_id != item.product_id:
                raise OrderTransitionError("Variante incohérente.")
            if not variant.product.is_active or not variant.is_active:
                raise OrderTransitionError("Produit ou variante inactif.")
            if variant.stock < item.quantity:
                raise OrderTransitionError(
                    f"Stock insuffisant pour la variante {variant.id}.",
                    "insufficient_stock",
                )
            ProductVariant.objects.filter(pk=variant.pk).update(
                stock=F("stock") - item.quantity
            )

    def _commit_or_consume_stock(self, order):
        reservation_active = bool(
            order.stock_reserved_at and not order.stock_released_at
        )
        if not reservation_active:
            self._consume_stock(order)
            return

        items, variants = self._locked_items_and_variants(order)
        for item in items:
            variant = variants[item.variant_id]
            if variant.product_id != item.product_id:
                raise OrderTransitionError("Variante incohérente.")
            Product.objects.filter(pk=variant.product_id).update(
                sales_count=F("sales_count") + item.quantity
            )

    def _release_reserved_stock(self, order):
        if (
            not order.stock_reserved_at
            or order.stock_released_at
            or order.stock_consumed_at
        ):
            return False
        items, variants = self._locked_items_and_variants(order)
        for item in items:
            ProductVariant.objects.filter(pk=variants[item.variant_id].pk).update(
                stock=F("stock") + item.quantity
            )
        return True

    def _locked_items_and_variants(self, order):
        items = list(order.items.select_for_update().order_by("variant_id", "id"))
        if not items or any(item.variant_id is None for item in items):
            raise OrderTransitionError("Ligne sans variante exploitable.")
        variants = {
            variant.id: variant
            for variant in ProductVariant.objects.select_for_update()
            .select_related("product")
            .filter(id__in=sorted({item.variant_id for item in items}))
            .order_by("id")
        }
        if len(variants) != len({item.variant_id for item in items}):
            raise OrderTransitionError("Variante introuvable.")
        return items, variants

    @staticmethod
    def _actor_role(actor):
        if actor is None:
            return "system"
        if actor.is_superuser:
            return "admin"
        if actor.is_staff:
            return "staff"
        return "customer"
