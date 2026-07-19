from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import User
from django.db import IntegrityError, close_old_connections
from django.test import TestCase, TransactionTestCase

from orders.models import MAX_CART_ITEM_QUANTITY, Order, OrderItem
from orders.services.cart_service import CartError, CartService
from orders.services.order_service import InsufficientStockError, OrderService
from payments.models import Payment
from products.models import Category, Color, Product, ProductVariant, Size
from users.models import Customer


class VariantCartRulesTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            user=User.objects.create_user("phase3@example.com")
        )
        category = Category.objects.create(name="Robes")
        self.product = Product.objects.create(
            name="Robe", category=category, price="1000.00"
        )
        self.black = Color.objects.create(name="Noir")
        self.red = Color.objects.create(name="Rouge")
        self.medium = Size.objects.create(name="M")
        self.variant = ProductVariant.objects.create(
            product=self.product, color=self.black, size=self.medium, stock=5, sku="R-N-M"
        )
        self.other_variant = ProductVariant.objects.create(
            product=self.product, color=self.red, size=self.medium, stock=7, sku="R-R-M"
        )
        self.service = CartService()

    def test_repeated_add_merges_exact_variant(self):
        first, created = self.service.add_variant(
            customer=self.customer, variant=self.variant, quantity=2
        )
        second, created_again = self.service.add_variant(
            customer=self.customer, variant=self.variant, quantity=1
        )
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(second.quantity, 3)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_inactive_and_excessive_inputs_are_rejected(self):
        self.variant.is_active = False
        self.variant.save(update_fields=["is_active"])
        with self.assertRaises(CartError):
            self.service.add_variant(customer=self.customer, variant=self.variant, quantity=1)
        self.variant.is_active = True
        self.variant.save(update_fields=["is_active"])
        with self.assertRaises(CartError):
            self.service.add_variant(
                customer=self.customer, variant=self.variant,
                quantity=MAX_CART_ITEM_QUANTITY + 1,
            )
        with self.assertRaises(CartError):
            self.service.add_variant(customer=self.customer, variant=self.variant, quantity=6)

    def test_fulfillment_decrements_only_selected_variant_and_preserves_snapshot(self):
        item, _ = self.service.add_variant(
            customer=self.customer, variant=self.variant, quantity=2
        )
        self.product.name = "Nouveau nom"
        self.product.save(update_fields=["name"])
        payment = Payment.objects.create(
            order=item.order, amount=Decimal("2000.00"), payment_method="mock",
            provider="mock", status="completed", currency="XOF",
        )
        OrderService().fulfill_order(item.order, payment)
        self.variant.refresh_from_db()
        self.other_variant.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)
        self.assertEqual(self.other_variant.stock, 7)
        self.assertEqual(item.product_name, "Robe")

    def test_database_rejects_second_active_cart(self):
        Order.objects.create(customer=self.customer, complete=False)
        with self.assertRaises(IntegrityError):
            Order.objects.create(customer=self.customer, complete=False)


class PostgreSQLConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.customer_one = Customer.objects.create(
            user=User.objects.create_user("concurrent-one@example.com")
        )
        self.customer_two = Customer.objects.create(
            user=User.objects.create_user("concurrent-two@example.com")
        )
        category = Category.objects.create(name="Concurrency")
        product = Product.objects.create(name="Dernier article", category=category, price="500")
        self.variant = ProductVariant.objects.create(product=product, stock=1)

    def _run_fulfillment(self, order_id, payment_id, barrier):
        close_old_connections()
        barrier.wait()
        try:
            OrderService().fulfill_order(
                Order.objects.get(pk=order_id),
                Payment.objects.get(pk=payment_id),
            )
            return "paid"
        except InsufficientStockError:
            return "stock"
        finally:
            close_old_connections()

    def _create_cart(self, customer_id, barrier):
        close_old_connections()
        barrier.wait()
        try:
            customer = Customer.objects.get(pk=customer_id)
            return CartService().get_active_cart(
                customer, prefetch=False, create=True
            ).pk
        finally:
            close_old_connections()

    def _add_item(self, customer_id, variant_id, barrier):
        close_old_connections()
        barrier.wait()
        try:
            item, _ = CartService().add_variant(
                customer=Customer.objects.get(pk=customer_id),
                variant=ProductVariant.objects.get(pk=variant_id),
                quantity=1,
            )
            return item.pk
        finally:
            close_old_connections()

    def test_concurrent_cart_creation_converges_to_one_cart(self):
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(self._create_cart, self.customer_one.pk, barrier)
                for _ in range(2)
            ]
            ids = [future.result() for future in futures]
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(
            Order.objects.filter(customer=self.customer_one, complete=False).count(), 1
        )

    def test_concurrent_same_variant_add_creates_one_line(self):
        self.variant.stock = 10
        self.variant.save(update_fields=["stock"])
        Order.objects.create(customer=self.customer_one, complete=False)
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(
                    self._add_item, self.customer_one.pk, self.variant.pk, barrier
                )
                for _ in range(2)
            ]
            ids = [future.result() for future in futures]
        self.assertEqual(ids[0], ids[1])
        item = OrderItem.objects.get(pk=ids[0])
        self.assertEqual(item.quantity, 2)

    def test_two_real_transactions_cannot_consume_last_unit(self):
        orders = []
        payments = []
        for customer in (self.customer_one, self.customer_two):
            order = Order.objects.create(customer=customer, complete=False)
            OrderItem.objects.create(
                order=order, product=self.variant.product,
                variant=self.variant, quantity=1,
            )
            orders.append(order)
            payments.append(Payment.objects.create(
                order=order, amount=Decimal("500.00"), payment_method="mock",
                provider="mock", status="completed", currency="XOF",
            ))
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda pair: self._run_fulfillment(
                    pair[0].pk, pair[1].pk, barrier
                ), zip(orders, payments)
            ))
        self.variant.refresh_from_db()
        self.assertCountEqual(results, ["paid", "stock"])
        self.assertEqual(self.variant.stock, 0)
        self.assertEqual(Order.objects.filter(status=Order.STATUS_PAID).count(), 1)
