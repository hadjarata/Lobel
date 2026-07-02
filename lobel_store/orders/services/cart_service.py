import logging

from django.db import transaction

from orders.models import Order, OrderItem
from users.models import Customer

logger = logging.getLogger(__name__)


class CartService:
    """Gestion centralisée du panier actif (Order complete=False)."""

    def get_customer(self, user):
        if not user or not user.is_authenticated:
            return None
        customer, _ = Customer.objects.get_or_create(user=user)
        return customer

    def get_active_cart(self, customer, *, prefetch=True, create=False):
        if customer is None:
            return None

        queryset = Order.objects.filter(customer=customer, complete=False)
        if prefetch:
            queryset = queryset.prefetch_related("items__product")

        orders = list(queryset.order_by("-date_ordered"))
        if not orders:
            if create:
                return Order.objects.create(customer=customer, complete=False)
            return None

        primary = next((order for order in orders if order.items.exists()), orders[0])
        duplicates = [order for order in orders if order.pk != primary.pk]

        if duplicates:
            self._merge_duplicate_carts(primary, duplicates)
            logger.info(
                "Merged duplicate incomplete orders into cart=%s for customer=%s",
                primary.id,
                customer.id,
            )

        if prefetch:
            return (
                Order.objects.filter(pk=primary.pk)
                .prefetch_related("items__product")
                .first()
            )

        return primary

    @transaction.atomic
    def _merge_duplicate_carts(self, primary: Order, duplicates: list[Order]) -> None:
        primary = Order.objects.select_for_update().get(pk=primary.pk)

        for duplicate in duplicates:
            duplicate = Order.objects.select_for_update().get(pk=duplicate.pk)
            for item in duplicate.items.select_for_update().all():
                existing = primary.items.filter(product_id=item.product_id).first()
                if existing:
                    existing.quantity += item.quantity
                    existing.save(update_fields=["quantity"])
                else:
                    item.order = primary
                    item.save(update_fields=["order"])
            duplicate.delete()

    def empty_cart_payload(self):
        return {
            "id": None,
            "items": [],
            "cart_total": 0,
            "cart_items": 0,
            "complete": False,
            "status": Order.STATUS_PENDING,
        }

    def log_cart_state(self, action, user, order=None):
        item_count = order.items.count() if order else 0
        logger.info(
            "[Cart Debug] %s user=%s order_id=%s total_items=%s",
            action,
            getattr(user, "id", None),
            getattr(order, "id", None),
            item_count,
        )
