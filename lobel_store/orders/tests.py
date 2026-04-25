from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem
from products.models import Category, Product
from users.models import Customer


class OrderItemViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cart@example.com",
            email="cart@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.category = Category.objects.create(name="Shoes")
        self.product = Product.objects.create(
            name="Runner",
            category=self.category,
            price="49.99",
        )
        self.url = reverse("orderitem-list")

    def test_create_order_item_creates_pending_order_when_missing(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.filter(customer=self.customer, complete=False).count(), 1)

        order = Order.objects.get(customer=self.customer, complete=False)
        item = OrderItem.objects.get(order=order)

        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

    def test_create_order_item_reuses_existing_pending_order(self):
        existing_order = Order.objects.create(customer=self.customer, complete=False)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"product_id": self.product.id, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.filter(customer=self.customer, complete=False).count(), 1)

        item = OrderItem.objects.get(order=existing_order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 1)
