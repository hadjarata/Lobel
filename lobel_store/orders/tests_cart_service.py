from django.contrib.auth.models import User
from django.test import TestCase

from orders.models import Order, OrderItem
from orders.services.cart_service import CartService
from products.models import Category, Product, ProductVariant
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
        self.variant = ProductVariant.objects.create(product=self.product, stock=20)

    def test_get_active_cart_returns_existing_cart(self):
        order_with_items = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=order_with_items, product=self.product, quantity=3)

        cart = self.service.get_active_cart(self.customer, prefetch=True, create=False)

        self.assertEqual(cart.id, order_with_items.id)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(Order.objects.filter(customer=self.customer, complete=False).count(), 1)

    def test_get_active_cart_create_reuses_existing(self):
        existing = Order.objects.create(customer=self.customer, complete=False)
        cart = self.service.get_active_cart(self.customer, prefetch=False, create=True)
        self.assertEqual(cart.id, existing.id)
        self.assertEqual(Order.objects.filter(customer=self.customer, complete=False).count(), 1)

    def test_get_customer_creates_customer_when_missing(self):
        user = User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="password123",
        )

        customer = self.service.get_customer(user)

        self.assertIsNotNone(customer)
        self.assertEqual(customer.user, user)
