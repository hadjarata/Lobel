import logging
from decimal import Decimal, ROUND_HALF_UP

from orders.models import Order
from orders.services.cart_service import CartService
from payments.models import Payment
from payments.providers import get_payment_provider
from payments.providers.base import (
    CheckoutContext,
    PaymentProviderError,
    PaymentProvider,
)
from users.models import Customer

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

        amount = self._format_amount(order.get_cart_total)
        currency = "XOF"
        order_reference = self._build_order_reference(order)
        provider_name = self.payment_provider.provider_name

        payment = Payment.objects.create(
            order=order,
            amount=order.get_cart_total,
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

    def _get_active_cart(self, user) -> Order | None:
        customer = self.cart_service.get_customer(user)
        if customer is None:
            return None

        return self.cart_service.get_active_cart(customer, prefetch=True, create=False)

    def _format_amount(self, amount: Decimal) -> int:
        return int(Decimal(amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _build_order_reference(self, order: Order) -> str:
        return f"LOBEL-ORDER-{order.id}"

    def _get_customer_country(self, customer: Customer | None) -> str | None:
        if not customer or not customer.country:
            return None
        return customer.country[:2].upper()
