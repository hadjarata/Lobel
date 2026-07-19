import logging
from decimal import Decimal, ROUND_HALF_UP

from orders.models import Order
from orders.models import MAX_CART_ITEM_QUANTITY
from orders.services.snapshot_service import FinancialSnapshotService, ORDER_CURRENCY
from orders.services.lifecycle_service import OrderLifecycleService
from orders.services.cart_service import CartService
from payments.models import Payment
from payments.providers import get_payment_provider
from payments.providers.base import (
    CheckoutContext,
    PaymentProviderError,
    PaymentProvider,
)
from users.models import Customer
from django.db import transaction
from django.utils import timezone
from products.models import ProductVariant

logger = logging.getLogger(__name__)


class CheckoutError(Exception):
    pass


class EmptyCartError(CheckoutError):
    pass


class CheckoutService:
    def __init__(
        self,
        payment_provider: PaymentProvider | None = None,
        cart_service: CartService | None = None,
    ):
        self.payment_provider = payment_provider or get_payment_provider()
        self.cart_service = cart_service or CartService()

    def create_checkout_session(self, user, frontend_url: str = "") -> dict:
        order = self._get_active_cart(user)
        if order is None or not order.items.exists():
            raise EmptyCartError("Le panier est vide.")
        if order.status == Order.STATUS_CART:
            self._validate_cart_for_checkout(order, user)

        order.refresh_from_db()
        amount = self._format_amount(order.total_amount)
        currency = order.currency
        order_reference = self._build_order_reference(order)
        provider_name = self.payment_provider.provider_name

        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            payment_method=provider_name,
            provider=provider_name,
            status="pending",
            currency=currency,
            order_reference=order_reference,
        )

        context = CheckoutContext(
            payment=payment,
            order=order,
            amount=amount,
            currency=currency,
            order_reference=order_reference,
            description=f"Commande LobelStore #{order.id}",
            customer_email=user.email or "",
            customer_firstname=user.first_name or "Client",
            customer_lastname=user.last_name or "LobelStore",
            frontend_url=frontend_url,
        )

        try:
            session = self.payment_provider.create_checkout(context)
        except PaymentProviderError:
            payment.status = "failed"
            payment.save(update_fields=["status"])
            logger.warning(
                "[Payment] checkout failed - payment_id=%s order_id=%s",
                payment.id,
                order.id,
            )
            raise

        payment.session_token = session.session_token
        payment.save(update_fields=["session_token"])

        logger.info(
            "[Payment] checkout session ready - payment_id=%s order_id=%s",
            payment.id,
            order.id,
        )

        return {
            "payment_url": session.payment_url,
            "sessionToken": session.session_token,
            "paymentId": payment.id,
        }

    @transaction.atomic
    def _validate_cart_for_checkout(self, order, user):
        order = Order.objects.select_for_update().get(
            pk=order.pk, status=Order.STATUS_CART
        )
        items = list(order.items.select_for_update().order_by("variant_id", "id"))
        if not items or any(item.variant_id is None for item in items):
            raise CheckoutError("Le panier contient une ligne sans variante valide.")
        variants = {
            variant.pk: variant
            for variant in ProductVariant.objects.select_for_update()
            .select_related("product")
            .filter(pk__in=sorted({item.variant_id for item in items}))
            .order_by("id")
        }
        for item in items:
            variant = variants.get(item.variant_id)
            if not variant or variant.product_id != item.product_id:
                raise CheckoutError("Une variante ne correspond pas au produit.")
            if not variant.product.is_active or not variant.is_active:
                raise CheckoutError("Un produit ou une variante est inactif.")
            if not 1 <= item.quantity <= MAX_CART_ITEM_QUANTITY:
                raise CheckoutError("Quantité invalide.")
            if item.quantity > variant.stock:
                raise CheckoutError(
                    f"Stock insuffisant pour la variante {variant.id} "
                    f"(disponible : {variant.stock})."
                )
            item.product_name = variant.product.name
            item.color_name = variant.color.name if variant.color else ""
            item.size_name = variant.size.name if variant.size else ""
            item.sku = variant.sku
            item.unit_price = variant.effective_price
            item.product_reference = variant.product_id
            item.variant_reference = variant.id
            item.variant_name = " / ".join(
                value for value in (
                    item.color_name, item.size_name
                ) if value
            )
            item.currency = ORDER_CURRENCY
            item.discount_amount = Decimal("0.00")
            item.subtotal = FinancialSnapshotService.line_subtotal(
                unit_price=item.unit_price,
                quantity=item.quantity,
                discount_amount=item.discount_amount,
            )
            item.save(update_fields=[
                "product_name", "color_name", "size_name", "sku", "unit_price",
                "product_reference", "variant_reference", "variant_name",
                "currency", "discount_amount", "subtotal",
            ])

        subtotal = sum((item.subtotal for item in items), Decimal("0.00"))
        shipping = Decimal("0.00")
        discount = Decimal("0.00")
        total = FinancialSnapshotService.order_total(
            subtotal=subtotal,
            shipping_amount=shipping,
            discount_amount=discount,
        )
        user = order.customer.user if order.customer_id else None
        full_name = user.get_full_name().strip() if user else ""
        order.customer_name = full_name or (user.username if user else "")
        order.customer_email = user.email if user else ""
        order.delivery_recipient_name = order.customer_name
        order.delivery_phone = order.customer.phone_number if order.customer_id else ""
        order.delivery_address = order.customer.address if order.customer_id else ""
        order.delivery_country = order.customer.country if order.customer_id else ""
        order.subtotal_amount = subtotal
        order.shipping_amount = shipping
        order.discount_amount = discount
        order.total_amount = total
        order.currency = ORDER_CURRENCY
        order.snapshot_at = timezone.now()
        order.save(update_fields=[
            "customer_name", "customer_email", "delivery_recipient_name",
            "delivery_phone", "delivery_address", "delivery_country",
            "subtotal_amount", "shipping_amount", "discount_amount",
            "total_amount", "currency", "snapshot_at",
        ])
        OrderLifecycleService().transition_order(
            order=order,
            target_status=Order.STATUS_PENDING_PAYMENT,
            actor=user,
            reason_code="checkout_completed",
        )

    def _get_active_cart(self, user) -> Order | None:
        customer = self.cart_service.get_customer(user)
        if customer is None:
            return None

        return (
            Order.objects.filter(
                customer=customer,
                status__in=[Order.STATUS_CART, Order.STATUS_PENDING_PAYMENT],
            )
            .prefetch_related("items__variant", "items__product")
            .order_by("-date_ordered")
            .first()
        )

    def _format_amount(self, amount: Decimal) -> int:
        return int(Decimal(amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _build_order_reference(self, order: Order) -> str:
        return f"LOBEL-ORDER-{order.id}"

    def _get_customer_country(self, customer: Customer | None) -> str | None:
        if not customer or not customer.country:
            return None
        return customer.country[:2].upper()
