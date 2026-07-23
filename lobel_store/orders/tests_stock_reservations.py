from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from orders.models import Order
from orders.services.cart_service import CartService
from orders.services.expiration_service import OrderExpirationService
from orders.services.lifecycle_service import OrderLifecycleService, OrderTransitionError
from payments.models import Payment
from payments.services.payment_service import PaymentService
from products.models import Category, Product, ProductVariant
from users.models import Customer


class StockReservationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Réservations")
        self.product = Product.objects.create(
            name="Pièce unique",
            category=self.category,
            price=Decimal("1000.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            stock=1,
        )

    def make_cart(self, email):
        user = User.objects.create_user(email)
        customer = Customer.objects.create(user=user)
        item, _ = CartService().add_variant(
            customer=customer,
            variant=self.variant,
            quantity=1,
        )
        order = item.order
        order.snapshot_at = timezone.now()
        order.subtotal_amount = Decimal("1000.00")
        order.total_amount = Decimal("1000.00")
        order.customer_email = email
        order.delivery_recipient_name = "Client Test"
        order.save(update_fields=[
            "snapshot_at", "subtotal_amount", "total_amount",
            "customer_email", "delivery_recipient_name",
        ])
        return user, order

    def reserve(self, user, order):
        return OrderLifecycleService().transition_order(
            order=order,
            target_status=Order.STATUS_PENDING_PAYMENT,
            actor=user,
            reason_code="checkout_order_created",
        )[0]

    def test_first_order_reserves_last_unit_and_second_is_refused(self):
        first_user, first_order = self.make_cart("first-reservation@example.com")
        second_user, second_order = self.make_cart("second-reservation@example.com")

        self.reserve(first_user, first_order)
        with self.assertRaises(OrderTransitionError) as raised:
            self.reserve(second_user, second_order)

        self.assertEqual(raised.exception.code, "insufficient_stock")
        self.variant.refresh_from_db()
        second_order.refresh_from_db()
        self.assertEqual(self.variant.stock, 0)
        self.assertEqual(second_order.status, Order.STATUS_CART)

    def test_payment_commits_reservation_without_second_decrement(self):
        user, order = self.make_cart("paid-reservation@example.com")
        order = self.reserve(user, order)
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            currency=order.currency,
            payment_method="mock",
            provider="mock",
            status="completed",
        )

        PaymentService().handle_payment_completed(payment)

        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertIsNotNone(order.stock_consumed_at)
        self.assertEqual(self.variant.stock, 0)
        self.assertEqual(self.product.sales_count, 1)

    def test_expiration_releases_reservation(self):
        user, order = self.make_cart("expired-reservation@example.com")
        order = self.reserve(user, order)

        OrderExpirationService().expire(order)

        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_EXPIRED)
        self.assertIsNotNone(order.stock_released_at)
        self.assertEqual(self.variant.stock, 1)

    def test_confirmed_legacy_payment_without_stock_requires_refund(self):
        user, order = self.make_cart("legacy-no-stock@example.com")
        order = self.reserve(user, order)
        Order.objects.filter(pk=order.pk).update(
            stock_reserved_at=None,
            stock_reservation_expires_at=None,
        )
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            currency=order.currency,
            payment_method="mock",
            provider="mock",
            status="completed",
        )

        PaymentService().handle_payment_completed(payment)

        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_REFUND_REQUIRED)
        self.assertEqual(payment.failure_code, "payment_refund_required")
        self.assertIsNotNone(payment.processed_at)
