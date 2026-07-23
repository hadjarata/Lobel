from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from orders.models import Order, OrderItem
from payments.models import Payment, PaymentOperationalAlert
from payments.services.payment_service import PaymentService
from products.models import Category, Product, ProductVariant
from users.models import Customer


class DuplicatePaymentFixture:
    def make_data(self):
        user = User.objects.create_user(f"duplicate-{User.objects.count()}@example.com")
        customer = Customer.objects.create(user=user)
        category = Category.objects.create(name=f"Double paiement {user.id}")
        product = Product.objects.create(
            name="Article",
            category=category,
            price=Decimal("1000.00"),
        )
        variant = ProductVariant.objects.create(product=product, stock=2)
        order = Order.objects.create(
            customer=customer,
            status=Order.STATUS_PENDING_PAYMENT,
            snapshot_at=timezone.now(),
            customer_name="Client",
            customer_email=user.email,
            delivery_recipient_name="Client Test",
            subtotal_amount=Decimal("1000.00"),
            total_amount=Decimal("1000.00"),
            currency="XOF",
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=1,
            product_name=product.name,
            unit_price=Decimal("1000.00"),
            subtotal=Decimal("1000.00"),
            currency="XOF",
        )
        payments = [
            Payment.objects.create(
                order=order,
                amount=order.total_amount,
                currency=order.currency,
                payment_method="mock",
                provider="mock",
                status="completed",
                provider_status="completed",
                external_transaction_id=f"TX-DUP-{order.id}-{index}",
            )
            for index in (1, 2)
        ]
        return order, product, variant, payments


class DuplicatePaymentTests(DuplicatePaymentFixture, TestCase):
    def test_second_confirmation_requires_refund_without_second_fulfillment(self):
        order, product, variant, payments = self.make_data()

        first_outcome = PaymentService().handle_payment_completed(payments[0])
        second_outcome = PaymentService().handle_payment_completed(payments[1])

        order.refresh_from_db()
        product.refresh_from_db()
        variant.refresh_from_db()
        payments[0].refresh_from_db()
        payments[1].refresh_from_db()

        self.assertEqual(first_outcome, "completed")
        self.assertEqual(second_outcome, "refund_required")
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(variant.stock, 1)
        self.assertEqual(product.sales_count, 1)
        self.assertEqual(payments[0].status, "completed")
        self.assertEqual(payments[1].status, "refund_required")
        self.assertEqual(payments[1].provider_status, "completed")
        self.assertEqual(payments[1].failure_code, "duplicate_payment")
        self.assertIsNotNone(payments[1].processed_at)
        self.assertEqual(
            payments[1].audit_events.filter(
                event_type="duplicate_payment_detected",
                to_status="refund_required",
            ).count(),
            1,
        )
        alert = PaymentOperationalAlert.objects.get(payment=payments[1])
        self.assertEqual(alert.status, "open")
        self.assertEqual(alert.severity, "critical")
        self.assertEqual(alert.metadata["primary_payment_id"], payments[0].id)

    def test_reprocessing_duplicate_is_idempotent(self):
        _, _, _, payments = self.make_data()
        PaymentService().handle_payment_completed(payments[0])
        PaymentService().handle_payment_completed(payments[1])

        outcome = PaymentService().handle_payment_completed(payments[1])

        self.assertEqual(outcome, "refund_required")
        self.assertEqual(
            PaymentOperationalAlert.objects.filter(payment=payments[1]).count(),
            1,
        )
        self.assertEqual(
            payments[1].audit_events.filter(
                event_type="duplicate_payment_detected"
            ).count(),
            1,
        )


class ConcurrentDuplicatePaymentTests(DuplicatePaymentFixture, TransactionTestCase):
    reset_sequences = True

    @staticmethod
    def _confirm(payment_id, barrier):
        close_old_connections()
        barrier.wait()
        try:
            payment = Payment.objects.get(pk=payment_id)
            return payment_id, PaymentService().handle_payment_completed(payment)
        finally:
            close_old_connections()

    def test_concurrent_confirmations_choose_one_commercial_payment(self):
        order, product, variant, payments = self.make_data()
        barrier = Barrier(2)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                future.result()
                for future in (
                    pool.submit(self._confirm, payments[0].id, barrier),
                    pool.submit(self._confirm, payments[1].id, barrier),
                )
            ]

        order.refresh_from_db()
        product.refresh_from_db()
        variant.refresh_from_db()
        statuses = list(
            Payment.objects.filter(order=order)
            .order_by("id")
            .values_list("status", flat=True)
        )
        self.assertCountEqual(
            [outcome for _, outcome in results],
            ["completed", "refund_required"],
        )
        self.assertCountEqual(statuses, ["completed", "refund_required"])
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(variant.stock, 1)
        self.assertEqual(product.sales_count, 1)
        self.assertEqual(
            PaymentOperationalAlert.objects.filter(
                order=order,
                alert_type="duplicate_payment",
                status="open",
            ).count(),
            1,
        )
