import logging

from django.db import IntegrityError, transaction

from orders.models import MAX_CART_ITEM_QUANTITY, Order, OrderItem
from products.models import ProductVariant
from users.models import Customer

logger = logging.getLogger(__name__)


class CartError(Exception):
    pass


class CartService:
    def get_customer(self, user):
        if not user or not user.is_authenticated:
            return None
        customer, _ = Customer.objects.get_or_create(user=user)
        return customer

    def get_active_cart(self, customer, *, prefetch=True, create=False):
        if customer is None:
            return None
        queryset = Order.objects.filter(customer=customer, status=Order.STATUS_CART)
        if prefetch:
            queryset = queryset.prefetch_related(
                "items__product__media_files", "items__variant__color", "items__variant__size"
            )
        cart = queryset.first()
        if cart is None and create:
            try:
                with transaction.atomic():
                    cart = Order.objects.create(customer=customer, complete=False)
            except IntegrityError:
                cart = Order.objects.get(customer=customer, complete=False)
        return cart

    @transaction.atomic
    def add_variant(self, *, customer, variant, quantity):
        self._validate_quantity(quantity)
        variant = ProductVariant.objects.select_related("product", "color", "size").get(pk=variant.pk)
        self._validate_variant(variant, quantity)
        cart = self.get_active_cart(customer, prefetch=False, create=True)
        cart = Order.objects.select_for_update().get(pk=cart.pk)
        if cart.snapshot_at:
            raise CartError("Cette commande est déjà figée.")
        item = OrderItem.objects.select_for_update().filter(order=cart, variant=variant).first()
        final_quantity = quantity + (item.quantity if item else 0)
        self._validate_quantity(final_quantity)
        self._validate_variant(variant, final_quantity)
        snapshots = self._snapshots(variant)
        if item:
            item.quantity = final_quantity
            for name, value in snapshots.items():
                setattr(item, name, value)
            item.save(update_fields=["quantity", *snapshots.keys()])
            return item, False
        try:
            return OrderItem.objects.create(
                order=cart, product=variant.product, variant=variant,
                quantity=quantity, **snapshots
            ), True
        except IntegrityError:
            item = OrderItem.objects.select_for_update().get(order=cart, variant=variant)
            item.quantity += quantity
            self._validate_quantity(item.quantity)
            self._validate_variant(variant, item.quantity)
            item.save(update_fields=["quantity"])
            return item, False

    @transaction.atomic
    def update_quantity(self, *, item, customer, quantity):
        self._validate_quantity(quantity)
        item = OrderItem.objects.select_for_update().get(
            pk=item.pk, order__customer=customer, order__complete=False
        )
        if item.order.snapshot_at:
            raise CartError("Cette commande est déjà figée.")
        if item.variant is None:
            raise CartError("Cette ligne historique ne peut pas être modifiée.")
        self._validate_variant(item.variant, quantity)
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        return item

    def _validate_quantity(self, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= MAX_CART_ITEM_QUANTITY:
            raise CartError(f"La quantité doit être comprise entre 1 et {MAX_CART_ITEM_QUANTITY}.")

    def _validate_variant(self, variant, quantity):
        if not variant.product.is_active:
            raise CartError("Ce produit est inactif.")
        if not variant.is_active:
            raise CartError("Cette variante est inactive.")
        if quantity > variant.stock:
            raise CartError(f"Stock insuffisant (disponible : {variant.stock}).")

    def _snapshots(self, variant):
        return {
            "product_name": variant.product.name,
            "product_reference": variant.product_id,
            "variant_reference": variant.id,
            "variant_name": " / ".join(
                value for value in (
                    variant.color.name if variant.color else "",
                    variant.size.name if variant.size else "",
                ) if value
            ),
            "color_name": variant.color.name if variant.color else "",
            "size_name": variant.size.name if variant.size else "",
            "sku": variant.sku,
            "unit_price": variant.effective_price,
            "currency": "XOF",
        }

    def empty_cart_payload(self):
        return {"id": None, "items": [], "cart_total": 0, "cart_items": 0,
                "complete": False, "status": Order.STATUS_CART}

    def log_cart_state(self, action, user, order=None):
        logger.info("[Cart] %s user=%s order=%s", action, getattr(user, "id", None),
                    getattr(order, "id", None))
