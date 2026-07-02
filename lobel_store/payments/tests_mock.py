import json
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem
from payments.models import Payment
from products.models import Category, Product, ProductVariant
from users.models import Customer


MOCK_SETTINGS = {
    "PAYMENT_PROVIDER": "mock",
    "FRONTEND_URL": "http://localhost:5173",
}


@override_settings(**MOCK_SETTINGS)
class MockCheckoutFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mock@example.com",
            email="mock@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Shoes")
        self.product = Product.objects.create(
            name="Runner",
            category=self.category,
            price="500.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=10)
        self.order = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2)
        self.checkout_url = reverse("payment-checkout")
        self.confirm_url = reverse("payment-mock-confirm")

    def test_mock_checkout_returns_payment_url_and_creates_pending_payment(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.checkout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("payment_url", response.data)
        self.assertIn("mock=true", response.data["payment_url"])
        self.assertIn("/checkout/success", response.data["payment_url"])
        self.assertEqual(response.data["orderId"], self.order.id)

        payment = Payment.objects.get(id=response.data["paymentId"])
        self.assertEqual(payment.provider, "mock")
        self.assertEqual(payment.status, "pending")
        self.assertTrue(payment.session_token.startswith("mock_"))

    def test_mock_confirm_marks_payment_and_order_as_completed(self):
        payment = Payment.objects.create(
            order=self.order,
            amount="1000.00",
            payment_method="mock",
            provider="mock",
            status="pending",
            session_token="mock_token_confirm",
            order_reference=f"LOBEL-ORDER-{self.order.id}",
            currency="XOF",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.confirm_url,
            {"paymentId": payment.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.order.refresh_from_db()
        self.variant.refresh_from_db()

        self.assertEqual(payment.status, "completed")
        self.assertIsNotNone(payment.processed_at)
        self.assertTrue(self.order.complete)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(self.variant.stock, 8)

    def test_mock_confirm_is_idempotent(self):
        payment = Payment.objects.create(
            order=self.order,
            amount="1000.00",
            payment_method="mock",
            provider="mock",
            status="pending",
            session_token="mock_token_idempotent",
            order_reference=f"LOBEL-ORDER-{self.order.id}",
            currency="XOF",
        )
        self.client.force_authenticate(user=self.user)

        first = self.client.post(self.confirm_url, {"paymentId": payment.id}, format="json")
        second = self.client.post(self.confirm_url, {"paymentId": payment.id}, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 8)

    def test_mock_confirm_rejects_unknown_payment(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.confirm_url, {"paymentId": 99999}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_flow_add_to_cart_checkout_confirm(self):
        self.client.force_authenticate(user=self.user)

        checkout_response = self.client.post(self.checkout_url, {}, format="json")
        payment_id = checkout_response.data["paymentId"]

        confirm_response = self.client.post(
            self.confirm_url,
            {"paymentId": payment_id},
            format="json",
        )

        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_response.data["orderId"], self.order.id)

        self.order.refresh_from_db()
        self.assertTrue(self.order.complete)
