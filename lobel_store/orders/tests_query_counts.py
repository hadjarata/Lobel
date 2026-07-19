from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from products.models import Category, Color, Product, ProductVariant
from users.models import Customer
from .models import Order, OrderItem


class OrderQueryCountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("query-orders")
        self.customer = Customer.objects.create(user=self.user)
        product = Product.objects.create(
            name="Order query", category=Category.objects.create(name="Order query"), price=5
        )
        self.variant = ProductVariant.objects.create(product=product, stock=100)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def create_order(self):
        order = Order.objects.create(customer=self.customer, complete=True, status=Order.STATUS_PAID)
        OrderItem.objects.create(
            order=order, product=self.variant.product, variant=self.variant,
            quantity=1, unit_price=5,
        )
        return order

    def count(self, url):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, response.data)
        return len(captured)

    def test_order_list_query_count_is_stable(self):
        self.create_order()
        one = self.count("/api/orders/orders/")
        for _ in range(9):
            self.create_order()
        ten = self.count("/api/orders/orders/")
        self.assertLessEqual(ten, one)
        self.assertLessEqual(ten, 3)

    def test_order_detail_query_count_is_stable(self):
        order = self.create_order()
        one = self.count(f"/api/orders/orders/{order.pk}/")
        for _ in range(4):
            variant = ProductVariant.objects.create(
                product=self.variant.product,
                color=Color.objects.create(name=f"Order color {_}"),
                stock=1,
            )
            OrderItem.objects.create(order=order, product=variant.product, variant=variant, quantity=1, unit_price=5)
        many = self.count(f"/api/orders/orders/{order.pk}/")
        self.assertLessEqual(many, one)
