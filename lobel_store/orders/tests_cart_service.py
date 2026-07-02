from django.contrib.auth.models import User
from django.test import TestCase

from orders.models import Order, OrderItem
from orders.services.cart_service import CartService
from products.models import Category, Product
from users.models import Customer


class CartServiceTests(TestCase):
    def setUp(self):
        self.service = CartService()
        self.user = User.objects.create_user(
            username="cartservice@example.com",
            email="cartservice@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.category = Category.objects.create(name="Test")
        self.product = Product.objects.create(
            name="Item",
            category=self.category,
            price="50.00",
        )

    def test_get_active_cart_prefers_order_with_items_over_newer_empty_order(self):
        order_with_items = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=order_with_items, product=self.product, quantity=3)
        Order.objects.create(customer=self.customer, complete=False)

        cart = self.service.get_active_cart(self.customer, prefetch=True, create=False)

        self.assertEqual(cart.id, order_with_items.id)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(Order.objects.filter(customer=self.customer, complete=False).count(), 1)

    def test_get_active_cart_merges_duplicate_incomplete_orders(self):
        empty_order = Order.objects.create(customer=self.customer, complete=False)
        order_with_items = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=order_with_items, product=self.product, quantity=2)

        cart = self.service.get_active_cart(self.customer, prefetch=True, create=False)

        self.assertEqual(cart.id, order_with_items.id)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)
        self.assertEqual(Order.objects.filter(customer=self.customer, complete=False).count(), 1)
        self.assertFalse(Order.objects.filter(pk=empty_order.pk).exists())

    def test_get_customer_creates_customer_when_missing(self):
        user = User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="password123",
        )

        customer = self.service.get_customer(user)

        self.assertIsNotNone(customer)
        self.assertEqual(customer.user, user)
