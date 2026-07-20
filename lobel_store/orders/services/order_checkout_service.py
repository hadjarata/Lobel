import hashlib
import json
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from orders.models import (
    CheckoutCreationReceipt,
    MAX_CART_ITEM_QUANTITY,
    Order,
    OrderItem,
)
from orders.services.lifecycle_service import OrderLifecycleService
from orders.services.snapshot_service import FinancialSnapshotService, ORDER_CURRENCY
from products.models import ProductVariant
from users.models import Customer


class OrderCheckoutError(Exception):
    def __init__(self, detail, *, code="checkout_invalid", errors=None):
        super().__init__(detail)
        self.code = code
        self.errors = errors or []


class OrderCheckoutService:
    DELIVERY_METHODS = {
        "standard": {
            "code": "standard",
            "label": "Livraison standard",
            "fee": Decimal("3000.00"),
            "eta_min_days": 2,
            "eta_max_days": 5,
        },
        "express_bamako": {
            "code": "express_bamako",
            "label": "Livraison express Bamako",
            "fee": Decimal("1500.00"),
            "eta_min_days": 0,
            "eta_max_days": 1,
            "bamako_only": True,
        },
    }

    def delivery_options(self, address):
        city = self._text(address.get("city")).casefold()
        options = []
        for method in self.DELIVERY_METHODS.values():
            if method.get("bamako_only") and city != "bamako":
                continue
            options.append(self._public_method(method))
        return options

    def preview(self, user, payload):
        customer = self._customer(user)
        order = self._cart(customer)
        if order is None:
            raise OrderCheckoutError("Le panier est vide.", code="empty_cart")
        return self._build_preview(order, payload)

    @transaction.atomic
    def create_order(self, user, payload, idempotency_key):
        customer = Customer.objects.select_for_update().get(user=user)
        fingerprint = self._hash(payload)
        receipt = CheckoutCreationReceipt.objects.select_related("order").filter(
            customer=customer, idempotency_key=idempotency_key
        ).first()
        if receipt:
            if receipt.request_fingerprint != fingerprint:
                raise OrderCheckoutError(
                    "Cette clé d'idempotence a déjà été utilisée avec une autre requête.",
                    code="idempotency_conflict",
                )
            return receipt.order, True

        order = (
            Order.objects.select_for_update()
            .filter(customer=customer, status=Order.STATUS_CART)
            .order_by("-id")
            .first()
        )
        if order is None:
            pending = Order.objects.filter(
                customer=customer, status=Order.STATUS_PENDING_PAYMENT
            ).order_by("-id").first()
            raise OrderCheckoutError(
                "Une commande a déjà été créée depuis ce panier."
                if pending else "Le panier est vide.",
                code="order_already_created" if pending else "empty_cart",
            )

        preview = self._build_preview(order, payload, lock=True)
        if payload.get("checkout_version") != preview["checkout_version"]:
            raise OrderCheckoutError(
                "Le panier, le prix, le stock ou la livraison a changé. Actualisez le récapitulatif.",
                code="stale_checkout",
            )

        items = list(order.items.select_related(
            "variant__product", "variant__color", "variant__size"
        ).order_by("id"))
        preview_by_id = {line["line_id"]: line for line in preview["lines"]}
        for item in items:
            line = preview_by_id[item.id]
            variant = item.variant
            item.product_name = variant.product.name
            item.color_name = variant.color.name if variant.color else ""
            item.size_name = variant.size.name if variant.size else ""
            item.sku = variant.sku
            item.unit_price = Decimal(line["unit_price"])
            item.product_reference = variant.product_id
            item.variant_reference = variant.id
            item.variant_name = " / ".join(
                value for value in (item.color_name, item.size_name) if value
            )
            item.currency = ORDER_CURRENCY
            item.discount_amount = Decimal("0.00")
            item.subtotal = Decimal(line["line_total"])
            item.save()

        address = payload["shipping_address"]
        method = self._resolve_method(address, payload["delivery_method"])
        billing = address if payload["billing_same_as_shipping"] else payload["billing_address"]
        order.customer_name = user.get_full_name().strip() or user.username
        order.customer_email = user.email or ""
        order.delivery_recipient_name = address["recipient_name"]
        order.delivery_phone = address["phone"]
        order.delivery_country = address["country"]
        order.delivery_region = address.get("region", "")
        order.delivery_city = address["city"]
        order.delivery_district = address.get("district", "")
        order.delivery_street = address["street"]
        order.delivery_instructions = address.get("instructions", "")
        order.delivery_address = self._format_address(address)
        order.delivery_method_code = method["code"]
        order.delivery_method_label = method["label"]
        order.delivery_eta_min_days = method["eta_min_days"]
        order.delivery_eta_max_days = method["eta_max_days"]
        order.billing_same_as_shipping = payload["billing_same_as_shipping"]
        order.billing_address = self._format_address(billing)
        order.subtotal_amount = Decimal(preview["amounts"]["subtotal"])
        order.shipping_amount = Decimal(preview["amounts"]["shipping"])
        order.discount_amount = Decimal(preview["amounts"]["discount"])
        order.total_amount = Decimal(preview["amounts"]["total"])
        order.currency = ORDER_CURRENCY
        order.checkout_version = preview["checkout_version"]
        order.snapshot_at = timezone.now()
        order.save()
        OrderLifecycleService().transition_order(
            order=order,
            target_status=Order.STATUS_PENDING_PAYMENT,
            actor=user,
            reason_code="checkout_order_created",
        )
        try:
            CheckoutCreationReceipt.objects.create(
                customer=customer,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                order=order,
            )
        except IntegrityError:
            receipt = CheckoutCreationReceipt.objects.get(
                customer=customer, idempotency_key=idempotency_key
            )
            if receipt.request_fingerprint != fingerprint:
                raise OrderCheckoutError(
                    "Conflit d'idempotence.", code="idempotency_conflict"
                )
            return receipt.order, True
        return order, False

    def pending_order(self, user):
        return Order.objects.filter(
            customer__user=user, status=Order.STATUS_PENDING_PAYMENT
        ).prefetch_related("items", "status_history").order_by("-date_ordered", "-id").first()

    def _build_preview(self, order, payload, lock=False):
        address = payload["shipping_address"]
        method = self._resolve_method(address, payload["delivery_method"])
        item_query = order.items.select_related(
            "variant__product", "variant__color", "variant__size"
        ).order_by("id")
        items = list(item_query.select_for_update(of=("self",)) if lock else item_query)
        if not items:
            raise OrderCheckoutError("Le panier est vide.", code="empty_cart")
        variant_ids = sorted({item.variant_id for item in items if item.variant_id})
        variants_query = ProductVariant.objects.select_related(
            "product", "color", "size"
        ).filter(id__in=variant_ids).order_by("id")
        variants = {
            variant.id: variant
            for variant in (
                variants_query.select_for_update(of=("self",)) if lock else variants_query
            )
        }
        errors, warnings, lines = [], [], []
        subtotal = Decimal("0.00")
        version_lines = []
        for item in items:
            variant = variants.get(item.variant_id)
            line_errors = []
            if variant is None or variant.product_id != item.product_id:
                line_errors.append({"code": "invalid_variant", "detail": "Variante invalide."})
            elif not variant.product.is_active or not variant.is_active:
                line_errors.append({"code": "inactive", "detail": "Article indisponible."})
            elif not 1 <= item.quantity <= MAX_CART_ITEM_QUANTITY:
                line_errors.append({"code": "invalid_quantity", "detail": "Quantité invalide."})
            elif item.quantity > variant.stock:
                line_errors.append({
                    "code": "insufficient_stock",
                    "detail": "Stock insuffisant.",
                    "available_quantity": variant.stock,
                })
            if line_errors:
                errors.append({"line_id": item.id, "errors": line_errors})
                continue
            price = variant.effective_price
            line_total = FinancialSnapshotService.line_subtotal(
                unit_price=price, quantity=item.quantity, discount_amount=Decimal("0.00")
            )
            if item.unit_price is not None and item.unit_price != price:
                warnings.append({
                    "code": "price_changed",
                    "line_id": item.id,
                    "previous_price": str(item.unit_price),
                    "current_price": str(price),
                })
            subtotal += line_total
            lines.append({
                "line_id": item.id,
                "product_id": variant.product_id,
                "variant_id": variant.id,
                "product_name": variant.product.name,
                "variant_name": " / ".join(
                    value for value in (
                        variant.color.name if variant.color else "",
                        variant.size.name if variant.size else "",
                    ) if value
                ),
                "sku": variant.sku,
                "quantity": item.quantity,
                "unit_price": str(price),
                "line_total": str(line_total),
                "currency": ORDER_CURRENCY,
            })
            version_lines.append({
                "line_id": item.id, "variant_id": variant.id,
                "quantity": item.quantity, "price": str(price),
                "stock": variant.stock, "active": variant.is_active and variant.product.is_active,
            })
        if errors:
            raise OrderCheckoutError(
                "Le panier contient des articles invalides.",
                code="invalid_cart",
                errors=errors,
            )
        shipping = method["fee"]
        discount = Decimal("0.00")
        total = FinancialSnapshotService.order_total(
            subtotal=subtotal, shipping_amount=shipping, discount_amount=discount
        )
        version = self._hash({
            "lines": version_lines,
            "shipping_address": address,
            "delivery_method": method["code"],
            "shipping": str(shipping),
        })
        return {
            "lines": lines,
            "amounts": {
                "subtotal": str(subtotal),
                "shipping": str(shipping),
                "discount": str(discount),
                "tax": "0.00",
                "total": str(total),
                "currency": ORDER_CURRENCY,
            },
            "delivery_method": self._public_method(method),
            "warnings": warnings,
            "checkout_version": version,
        }

    def _resolve_method(self, address, code):
        available = {item["code"]: item for item in self.delivery_options(address)}
        if code not in available:
            raise OrderCheckoutError(
                "Mode de livraison indisponible pour cette adresse.",
                code="invalid_delivery_method",
            )
        return self.DELIVERY_METHODS[code]

    @staticmethod
    def _public_method(method):
        return {
            "code": method["code"], "label": method["label"],
            "fee": str(method["fee"]), "currency": ORDER_CURRENCY,
            "eta_min_days": method["eta_min_days"],
            "eta_max_days": method["eta_max_days"],
        }

    @staticmethod
    def _format_address(address):
        return ", ".join(filter(None, [
            address.get("street"), address.get("district"), address.get("city"),
            address.get("region"), address.get("country"),
        ]))

    @staticmethod
    def _text(value):
        return str(value or "").strip()

    @staticmethod
    def _hash(payload):
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _customer(user):
        try:
            return user.customer
        except Customer.DoesNotExist as exc:
            raise OrderCheckoutError("Profil client introuvable.", code="customer_missing") from exc

    @staticmethod
    def _cart(customer):
        return Order.objects.filter(
            customer=customer, status=Order.STATUS_CART
        ).order_by("-id").first()
