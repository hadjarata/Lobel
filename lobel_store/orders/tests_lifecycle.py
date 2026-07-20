from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order, OrderStatusHistory
from orders.services.cart_service import CartService
from orders.services.lifecycle_service import (
    OrderLifecycleService, OrderTransitionError,
)
from payments.models import Payment
from products.models import Category, Product, ProductVariant
from users.models import Customer


class LifecycleFixtureMixin:
    def make_order(self):
        self.owner = User.objects.create_user("owner-lifecycle@example.com")
        self.staff = User.objects.create_user(
            "staff-lifecycle@example.com", is_staff=True
        )
        self.customer = Customer.objects.create(user=self.owner)
        category = Category.objects.create(name="Lifecycle")
        self.product = Product.objects.create(
            name="Article", category=category, price=Decimal("100.00")
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=10)
        item, _ = CartService().add_variant(
            customer=self.customer, variant=self.variant, quantity=2
        )
        self.order = item.order
        self.order.snapshot_at = self.order.date_ordered
        self.order.subtotal_amount = Decimal("200.00")
        self.order.total_amount = Decimal("200.00")
        self.order.save(update_fields=["snapshot_at", "subtotal_amount", "total_amount"])
        self.service = OrderLifecycleService()
        return self.order

    def pending(self):
        self.service.transition_order(
            order=self.order, target_status=Order.STATUS_PENDING_PAYMENT,
            actor=self.owner, reason_code="checkout_completed",
        )
        self.order.refresh_from_db()

    def paid(self):
        self.pending()
        payment = Payment.objects.create(
            order=self.order, amount=self.order.total_amount,
            currency=self.order.currency, payment_method="mock",
            provider="mock", status="completed",
        )
        self.service.transition_order(
            order=self.order, target_status=Order.STATUS_PAID,
            payment=payment, reason_code="payment_verified",
        )
        self.order.refresh_from_db()
        return payment


class OrderLifecycleTests(LifecycleFixtureMixin, TestCase):
    def setUp(self):
        self.make_order()

    def test_authorized_logistics_transitions_are_traced(self):
        self.paid()
        for target in (
            Order.STATUS_PREPARING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED
        ):
            self.service.transition_order(
                order=self.order, target_status=target, actor=self.staff
            )
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, target)
        self.assertIsNotNone(self.order.preparation_started_at)
        self.assertIsNotNone(self.order.shipped_at)
        self.assertIsNotNone(self.order.delivered_at)
        self.assertEqual(
            list(self.order.status_history.values_list("to_status", flat=True)),
            ["pending_payment", "paid", "preparing", "shipped", "delivered"],
        )

    def test_invalid_transition_changes_nothing(self):
        with self.assertRaises(OrderTransitionError):
            self.service.transition_order(
                order=self.order, target_status=Order.STATUS_DELIVERED,
                actor=self.staff,
            )
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_CART)
        self.assertEqual(self.variant.stock, 10)
        self.assertFalse(OrderStatusHistory.objects.exists())

    def test_cancel_before_payment_does_not_release_stock(self):
        self.pending()
        self.service.transition_order(
            order=self.order, target_status=Order.STATUS_CANCELLED,
            actor=self.owner, reason_code="customer_request",
            reason_note="Mauvaise taille",
        )
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertIsNone(self.order.stock_consumed_at)
        self.assertIsNone(self.order.stock_released_at)
        self.assertEqual(self.variant.stock, 10)
        history = self.order.status_history.last()
        self.assertEqual(history.reason_code, "customer_request")
        self.assertEqual(history.actor, self.owner)

    def test_staff_cannot_cancel_paid_order_without_refund(self):
        self.paid()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 8)
        with self.assertRaises(OrderTransitionError):
            self.service.transition_order(
                order=self.order, target_status=Order.STATUS_CANCELLED,
                actor=self.staff, reason_code="operational_issue",
            )
        self.variant.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.variant.stock, 8)
        self.assertEqual(self.order.status, Order.STATUS_PAID)

    def test_refund_is_prepared_without_fake_provider_confirmation(self):
        self.paid()
        self.service.transition_order(
            order=self.order, target_status=Order.STATUS_REFUND_PENDING,
            actor=self.owner, reason_code="customer_request",
        )
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.refund_requested_at)
        with self.assertRaises(OrderTransitionError):
            self.service.transition_order(
                order=self.order, target_status=Order.STATUS_REFUNDED,
                actor=self.staff,
            )
        self.service.transition_order(
            order=self.order, target_status=Order.STATUS_REFUND_FAILED,
            actor=self.staff, reason_code="provider_unavailable",
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_REFUND_FAILED)

    def test_direct_status_save_is_blocked(self):
        self.order.status = Order.STATUS_DELIVERED
        with self.assertRaises(ValidationError):
            self.order.save(update_fields=["status"])


class LifecyclePermissionAPITests(LifecycleFixtureMixin, TestCase):
    def setUp(self):
        self.make_order()
        self.client = APIClient()

    def test_owner_can_cancel_own_pending_order_but_not_another_order(self):
        self.pending()
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            reverse("order-cancel", args=[self.order.id]),
            {"reason_code": "customer_request"}, format="json",
        )
        self.assertEqual(response.status_code, 200)

        other = User.objects.create_user("other-lifecycle@example.com")
        self.client.force_authenticate(other)
        response = self.client.post(
            reverse("order-cancel", args=[self.order.id]),
            {"reason_code": "customer_request"}, format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_customer_cannot_prepare_but_staff_can(self):
        self.paid()
        self.client.force_authenticate(self.owner)
        denied = self.client.post(reverse("order-prepare", args=[self.order.id]))
        self.assertEqual(denied.status_code, 403)
        self.client.force_authenticate(self.staff)
        allowed = self.client.post(reverse("order-prepare", args=[self.order.id]))
        self.assertEqual(allowed.status_code, 200)
