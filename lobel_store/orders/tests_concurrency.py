from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import TransactionTestCase

from orders.models import Order
from orders.services.cart_service import CartService
from orders.services.lifecycle_service import OrderLifecycleService, OrderTransitionError
from payments.models import Payment
from payments.services.payment_service import PaymentService
from products.models import Category, Product, ProductVariant
from users.models import Customer


class LifecycleConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user("race-owner@example.com")
        self.staff = User.objects.create_user("race-staff@example.com", is_staff=True)
        customer = Customer.objects.create(user=self.owner)
        category = Category.objects.create(name="Race")
        product = Product.objects.create(
            name="Race item", category=category, price=Decimal("100.00")
        )
        self.variant = ProductVariant.objects.create(product=product, stock=10)
        item, _ = CartService().add_variant(
            customer=customer, variant=self.variant, quantity=2
        )
        self.order = item.order
        self.order.snapshot_at = self.order.date_ordered
        self.order.total_amount = Decimal("200.00")
        self.order.subtotal_amount = Decimal("200.00")
        self.order.save(update_fields=["snapshot_at", "total_amount", "subtotal_amount"])
        OrderLifecycleService().transition_order(
            order=self.order, target_status=Order.STATUS_PENDING_PAYMENT,
            actor=self.owner,
        )
        self.payment = Payment.objects.create(
            order=self.order, amount=Decimal("200.00"), currency="XOF",
            payment_method="mock", provider="mock", status="completed",
        )
        OrderLifecycleService().transition_order(
            order=self.order, target_status=Order.STATUS_PAID,
            payment=self.payment,
        )

    def _cancel(self, barrier):
        close_old_connections()
        barrier.wait()
        try:
            _, changed = OrderLifecycleService().transition_order(
                order=Order.objects.get(pk=self.order.pk),
                target_status=Order.STATUS_CANCELLED,
                actor=User.objects.get(pk=self.staff.pk),
                reason_code="operational_issue",
            )
            return changed
        except OrderTransitionError:
            return False
        finally:
            close_old_connections()

    def _ship(self, barrier):
        close_old_connections()
        barrier.wait()
        try:
            _, changed = OrderLifecycleService().transition_order(
                order=Order.objects.get(pk=self.order.pk),
                target_status=Order.STATUS_SHIPPED,
                actor=User.objects.get(pk=self.staff.pk),
            )
            return changed
        finally:
            close_old_connections()

    def _pay_pending(self, order_id, payment_id, barrier):
        close_old_connections()
        barrier.wait()
        try:
            PaymentService().handle_payment_completed(
                Payment.objects.get(pk=payment_id)
            )
            return "paid"
        except Exception:
            return "payment_refused"
        finally:
            close_old_connections()

    def _cancel_pending(self, order_id, barrier):
        close_old_connections()
        barrier.wait()
        try:
            OrderLifecycleService().transition_order(
                order=Order.objects.get(pk=order_id),
                target_status=Order.STATUS_CANCELLED,
                actor=User.objects.get(pk=self.owner.pk),
                reason_code="customer_request",
            )
            return "cancelled"
        except OrderTransitionError:
            return "cancel_refused"
        finally:
            close_old_connections()

    def test_concurrent_paid_cancellation_is_refused(self):
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result() for future in [
                pool.submit(self._cancel, barrier), pool.submit(self._cancel, barrier)
            ]]
        self.variant.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(results, [False, False])
        self.assertEqual(self.variant.stock, 8)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(
            self.order.status_history.filter(to_status=Order.STATUS_CANCELLED).count(), 0
        )

    def test_double_ship_creates_one_transition(self):
        OrderLifecycleService().transition_order(
            order=self.order, target_status=Order.STATUS_PREPARING, actor=self.staff
        )
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result() for future in [
                pool.submit(self._ship, barrier), pool.submit(self._ship, barrier)
            ]]
        self.order.refresh_from_db()
        self.assertCountEqual(results, [True, False])
        self.assertEqual(self.order.status, Order.STATUS_SHIPPED)
        self.assertEqual(
            self.order.status_history.filter(to_status=Order.STATUS_SHIPPED).count(), 1
        )

    def test_payment_confirmation_racing_with_cancel_stays_coherent(self):
        other_user = User.objects.create_user("race-pending@example.com")
        customer = Customer.objects.create(user=other_user)
        item, _ = CartService().add_variant(
            customer=customer, variant=self.variant, quantity=1
        )
        order = item.order
        order.snapshot_at = order.date_ordered
        order.total_amount = Decimal("100.00")
        order.subtotal_amount = Decimal("100.00")
        order.save(update_fields=["snapshot_at", "total_amount", "subtotal_amount"])
        OrderLifecycleService().transition_order(
            order=order, target_status=Order.STATUS_PENDING_PAYMENT, actor=other_user
        )
        payment = Payment.objects.create(
            order=order, amount=Decimal("100.00"), currency="XOF",
            payment_method="mock", provider="mock", status="completed",
        )
        # Use the real owner of this second order in the cancellation thread.
        self.owner = other_user
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                pool.submit(self._pay_pending, order.pk, payment.pk, barrier),
                pool.submit(self._cancel_pending, order.pk, barrier),
            ]
            outcomes = [future.result() for future in results]
        order.refresh_from_db()
        self.variant.refresh_from_db()
        if order.status == Order.STATUS_PAID:
            self.assertIn("paid", outcomes)
            self.assertEqual(self.variant.stock, 7)
            self.assertIsNotNone(order.stock_consumed_at)
            self.assertIsNone(order.stock_released_at)
        else:
            self.assertEqual(order.status, Order.STATUS_REFUND_REQUIRED)
            self.assertIn("cancelled", outcomes)
            self.assertEqual(self.variant.stock, 8)
            self.assertIsNone(order.stock_consumed_at)
            self.assertIsNone(order.stock_released_at)
