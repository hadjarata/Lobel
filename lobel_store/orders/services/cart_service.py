import hashlib
import json
import logging

from django.db import IntegrityError, transaction

from orders.models import CartMergeReceipt, MAX_CART_ITEM_QUANTITY, Order, OrderItem
from products.models import ProductVariant
from users.models import Customer

logger = logging.getLogger(__name__)


class CartError(Exception):
    def __init__(self, message, *, code="cart_error", available_quantity=None):
        super().__init__(message)
        self.code = code
        self.available_quantity = available_quantity


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
                cart = Order.objects.get(customer=customer, status=Order.STATUS_CART)
        return cart

    @transaction.atomic
    def add_variant(self, *, customer, variant, quantity):
        self._validate_quantity(quantity)
        variant = ProductVariant.objects.select_related("product", "color", "size").get(pk=variant.pk)
        self._validate_variant(variant, quantity)
        cart = self.get_active_cart(customer, prefetch=False, create=True)
        cart = Order.objects.select_for_update().get(pk=cart.pk)
        if cart.snapshot_at:
            raise CartError("Cette commande est déjà figée.", code="cart_locked")
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
            raise CartError("Cette commande est déjà figée.", code="cart_locked")
        if item.variant is None:
            raise CartError("Cette ligne n'est plus modifiable.", code="invalid_variant")
        self._validate_variant(item.variant, quantity)
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        return item

    @transaction.atomic
    def clear_cart(self, customer):
        cart = self.get_active_cart(customer, prefetch=False, create=False)
        if cart is None:
            return None
        cart = Order.objects.select_for_update().get(pk=cart.pk)
        if cart.snapshot_at:
            raise CartError("Cette commande est déjà figée.", code="cart_locked")
        cart.items.all().delete()
        return cart

    @transaction.atomic
    def merge_guest_items(self, *, customer, items, idempotency_key):
        customer = Customer.objects.select_for_update().get(pk=customer.pk)
        canonical = json.dumps(items, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
        receipt = CartMergeReceipt.objects.select_for_update().filter(
            customer=customer, idempotency_key=idempotency_key
        ).first()
        if receipt:
            if receipt.request_fingerprint != fingerprint:
                raise CartError(
                    "Cette clé d'idempotence a déjà été utilisée.",
                    code="idempotency_conflict",
                )
            return receipt.response_payload, True

        totals = {}
        for item in items:
            totals[item["variant_id"]] = totals.get(item["variant_id"], 0) + item["quantity"]
        locked_variant_ids = list(
            ProductVariant.objects.select_for_update().filter(pk__in=totals)
            .values_list("pk", flat=True)
        )
        variants = {
            variant.pk: variant
            for variant in ProductVariant.objects.select_related(
                "product", "color", "size"
            ).filter(pk__in=locked_variant_ids)
        }
        merged, adjusted, rejected = [], [], []
        cart = self.get_active_cart(customer, prefetch=False, create=True)
        cart = Order.objects.select_for_update().get(pk=cart.pk)
        current = {
            item.variant_id: item.quantity
            for item in cart.items.select_for_update().filter(variant_id__in=totals)
        }
        for variant_id, requested in totals.items():
            variant = variants.get(variant_id)
            if variant is None:
                rejected.append(self._merge_rejection(
                    variant_id, requested, "invalid_variant", "Cette variante n'existe plus."
                ))
                continue
            try:
                self._validate_quantity(requested)
                self._validate_variant(variant, 1)
                accepted = min(requested, max(0, variant.stock - current.get(variant_id, 0)))
                if accepted < 1:
                    raise CartError(
                        "Stock insuffisant.", code="insufficient_stock",
                        available_quantity=max(0, variant.stock - current.get(variant_id, 0)),
                    )
                self.add_variant(customer=customer, variant=variant, quantity=accepted)
                report = {
                    "variant_id": variant_id,
                    "requested_quantity": requested,
                    "accepted_quantity": accepted,
                }
                (adjusted if accepted != requested else merged).append(report)
            except CartError as exc:
                rejected.append(self._merge_rejection(
                    variant_id, requested, exc.code, str(exc), exc.available_quantity
                ))
        payload = {
            "merged_items": merged, "adjusted_items": adjusted, "rejected_items": rejected,
        }
        CartMergeReceipt.objects.create(
            customer=customer, idempotency_key=idempotency_key,
            request_fingerprint=fingerprint, response_payload=payload,
        )
        return payload, False

    def _validate_quantity(self, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= MAX_CART_ITEM_QUANTITY:
            raise CartError(
                f"La quantité doit être comprise entre 1 et {MAX_CART_ITEM_QUANTITY}.",
                code="invalid_quantity",
            )

    def _validate_variant(self, variant, quantity):
        if not variant.product.is_active:
            raise CartError("Ce produit est inactif.", code="inactive_product")
        if not variant.is_active:
            raise CartError("Cette variante est inactive.", code="inactive_variant")
        if quantity > variant.stock:
            raise CartError(
                f"Stock insuffisant (disponible : {variant.stock}).",
                code="insufficient_stock", available_quantity=variant.stock,
            )

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

    def _merge_rejection(self, variant_id, requested, code, message, available=None):
        return {
            "variant_id": variant_id, "code": code, "message": message,
            "requested_quantity": requested, "accepted_quantity": 0,
            **({"available_quantity": available} if available is not None else {}),
        }

    def empty_cart_payload(self):
        return {
            "id": None, "items": [], "cart_total": 0, "cart_items": 0,
            "complete": False, "status": Order.STATUS_CART,
        }

    def log_cart_state(self, action, user, order=None):
        logger.info(
            "[Cart] %s user=%s order=%s", action,
            getattr(user, "id", None), getattr(order, "id", None),
        )
