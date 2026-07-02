import logging
import re

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from orders.models import Order
from payments.models import Payment
from products.models import Product, ProductVariant


logger = logging.getLogger(__name__)

ORDER_REFERENCE_PATTERN = re.compile(r"^LOBEL-ORDER-(\d+)$")


class OrderFulfillmentError(Exception):
    pass


class InsufficientStockError(OrderFulfillmentError):
    pass


class OrderService:
    @transaction.atomic
    def fulfill_order(self, order: Order, payment: Payment | None = None) -> None:
        order = Order.objects.select_for_update().get(pk=order.pk)

        if order.status == Order.STATUS_PAID:
            logger.info("Order already fulfilled - Order=%s", order.id)
            return

        if order.status in Order.TERMINAL_STATUSES:
            logger.info(
                "Order in terminal state, skipping fulfillment - Order=%s Status=%s",
                order.id,
                order.status,
            )
            return

        items = list(order.items.select_for_update().order_by("id"))
        if not items:
            raise OrderFulfillmentError(f"Order {order.id} has no items to fulfill.")

        if any(item.product_id is None for item in items):
            raise OrderFulfillmentError(
                f"Order {order.id} contains a deleted product."
            )

        product_ids = sorted({item.product_id for item in items})

        list(
            Product.objects.select_for_update()
            .filter(pk__in=product_ids)
            .order_by("id")
        )
        locked_variants = list(
            ProductVariant.objects.select_for_update()
            .filter(product_id__in=product_ids)
            .order_by("product_id", "id")
        )
        variants_by_product: dict[int, list[ProductVariant]] = {}
        for variant in locked_variants:
            variants_by_product.setdefault(variant.product_id, []).append(variant)

        for item in items:
            self._decrement_product_stock(
                item.product_id,
                item.quantity,
                variants_by_product.get(item.product_id, []),
            )
            Product.objects.filter(pk=item.product_id).update(
                sales_count=F("sales_count") + item.quantity
            )
            logger.info(
                "Stock updated - Order=%s Product=%s Quantity=%s",
                order.id,
                item.product_id,
                item.quantity,
            )

        order.status = Order.STATUS_PAID
        order.complete = True
        order.paid_at = timezone.now()
        if payment and payment.external_transaction_id:
            order.transaction_id = payment.external_transaction_id[:100]
        order.save(update_fields=["status", "complete", "paid_at", "transaction_id"])

        logger.info("Order fulfilled - Order=%s", order.id)

    def _decrement_product_stock(
        self,
        product_id: int,
        quantity: int,
        variants: list[ProductVariant],
    ) -> None:
        if not variants:
            raise InsufficientStockError(
                f"No stock variant configured for product {product_id}."
            )

        available_stock = sum(variant.stock for variant in variants)
        if available_stock < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for product {product_id}: "
                f"requested={quantity}, available={available_stock}."
            )

        remaining = quantity
        for variant in variants:
            if remaining <= 0:
                break
            if variant.stock == 0:
                continue

            deducted = min(variant.stock, remaining)
            updated_rows = ProductVariant.objects.filter(
                pk=variant.pk,
                stock__gte=deducted,
            ).update(stock=F("stock") - deducted)

            if updated_rows != 1:
                raise InsufficientStockError(
                    f"Concurrent stock conflict for product {product_id} "
                    f"on variant {variant.pk}."
                )

            variant.stock -= deducted
            remaining -= deducted

        if remaining > 0:
            raise InsufficientStockError(
                f"Insufficient stock for product {product_id} after atomic decrement."
            )

    @staticmethod
    def parse_order_id_from_reference(order_reference: str) -> int | None:
        match = ORDER_REFERENCE_PATTERN.match(order_reference)
        if not match:
            return None
        return int(match.group(1))
