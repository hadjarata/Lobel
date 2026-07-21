from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone

from orders.models import Order, OrderItem, OrderReceipt
from orders.services.receipt_service import OrderReceiptService
from payments.models import Payment
from users.models import Customer


class OrderReceiptConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        user = User.objects.create_user("receipt-concurrency@example.test")
        customer = Customer.objects.create(user=user)
        now = timezone.now()
        self.order = Order.objects.create(
            customer=customer,
            status=Order.STATUS_PAID,
            complete=True,
            snapshot_at=now - timedelta(minutes=2),
            paid_at=now,
            customer_name="Cliente",
            delivery_recipient_name="Cliente",
            delivery_address="Adresse figée",
            subtotal_amount=Decimal("1000.00"),
            shipping_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            currency="XOF",
        )
        OrderItem.objects.create(
            order=self.order,
            quantity=1,
            product_name="Produit historique",
            unit_price=Decimal("1000.00"),
            subtotal=Decimal("1000.00"),
            currency="XOF",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
            currency="XOF",
            payment_method="mock",
            provider="mock",
            status="completed",
            merchant_reference="LOBEL-CONCURRENT-RECEIPT",
        )

    def test_concurrent_issuance_creates_one_receipt_number(self):
        barrier = Barrier(2)

        def issue():
            close_old_connections()
            barrier.wait()
            receipt, _ = OrderReceiptService().issue(
                order=Order.objects.get(pk=self.order.pk),
                payment=Payment.objects.get(pk=self.payment.pk),
            )
            close_old_connections()
            return receipt.pk, receipt.receipt_number

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: issue(), range(2)))

        self.assertEqual(results[0], results[1])
        self.assertEqual(OrderReceipt.objects.filter(order=self.order).count(), 1)
