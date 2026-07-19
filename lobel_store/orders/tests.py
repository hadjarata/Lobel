from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from orders.models import Order, OrderItem
from payments.models import Payment
from payments.providers.base import CheckoutSessionResult
from products.models import Category, Product, ProductVariant
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
        self.variant = ProductVariant.objects.create(product=self.product, stock=20)
        self.url = reverse("orderitem-list")

    def test_create_order_item_creates_pending_order_when_missing(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"variant_id": self.variant.id, "quantity": 2},
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
            {"variant_id": self.variant.id, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.filter(customer=self.customer, complete=False).count(), 1)

        item = OrderItem.objects.get(order=existing_order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 1)


class CustomerResourceIsolationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.other_customer = Customer.objects.create(user=self.other_user)
        self.category = Category.objects.create(name="Bags")
        self.product = Product.objects.create(
            name="Tote",
            category=self.category,
            price="25.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=20)
        self.order = Order.objects.create(customer=self.customer, complete=False)
        self.other_order = Order.objects.create(customer=self.other_customer, complete=False)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
        )
        self.other_order_item = OrderItem.objects.create(
            order=self.other_order,
            product=self.product,
            quantity=1,
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount="25.00",
            payment_method="cash",
        )
        self.other_payment = Payment.objects.create(
            order=self.other_order,
            amount="25.00",
            payment_method="cash",
        )

    def test_orders_are_limited_to_authenticated_customer(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("order-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.order.id)

    def test_order_items_are_limited_to_authenticated_customer(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("orderitem-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.order_item.id)

    def test_payments_are_limited_to_authenticated_customer(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("payment-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.payment.id)

    def test_customer_cannot_retrieve_another_customers_order(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("order-detail", args=[self.other_order.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderListFilterTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="filters@example.com",
            email="filters@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.pending_order = Order.objects.create(
            customer=self.customer,
            complete=False,
            status=Order.STATUS_PENDING,
        )
        self.paid_order = Order.objects.create(
            customer=self.customer,
            complete=True,
            status=Order.STATUS_PAID,
        )
        self.url = reverse("order-list")

    def test_filter_orders_by_status_paid(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, {"status": Order.STATUS_PAID})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.paid_order.id)

    def test_filter_orders_by_complete_true(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, {"complete": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.paid_order.id)


class CartEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cart-endpoint@example.com",
            email="cart-endpoint@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.category = Category.objects.create(name="Accessories")
        self.product = Product.objects.create(
            name="Bag",
            category=self.category,
            price="100.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=20)
        self.url = reverse("order-cart")

    def test_cart_returns_active_incomplete_order(self):
        cart_order = Order.objects.create(customer=self.customer, complete=False)
        Order.objects.create(
            customer=self.customer,
            complete=True,
            status=Order.STATUS_PAID,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], cart_order.id)
        self.assertFalse(response.data["complete"])

    def test_cart_returns_empty_payload_when_no_active_cart(self):
        Order.objects.create(
            customer=self.customer,
            complete=True,
            status=Order.STATUS_PAID,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["id"])
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["cart_items"], 0)

    def test_cart_returns_items_from_active_order(self):
        order_with_items = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=order_with_items, product=self.product, quantity=2)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], order_with_items.id)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)
        self.assertEqual(response.data["cart_items"], 2)

    def test_cart_endpoint_creates_customer_if_missing(self):
        user_without_customer = User.objects.create_user(
            username="no-customer@example.com",
            email="no-customer@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=user_without_customer)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["id"])
        self.assertTrue(Customer.objects.filter(user=user_without_customer).exists())


class CartCheckoutFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="flow@example.com",
            email="flow@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Shoes")
        self.product = Product.objects.create(
            name="Runner",
            category=self.category,
            price="500.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=20)
        self.cart_url = reverse("order-cart")
        self.checkout_url = reverse("payment-checkout")
        self.order_item_url = reverse("orderitem-list")

    @override_settings(
        PAYMENT_PROVIDER="ligdicash",
        LIGDICASH_API_KEY="test-api-key",
        LIGDICASH_API_TOKEN="test-api-token",
        LIGDICASH_BASE_URL="https://app.ligdicash.com",
        LIGDICASH_STORE_NAME="LobelStore",
        LIGDICASH_STORE_URL="http://localhost:5173",
        LIGDICASH_RETURN_URL="http://localhost:5173/checkout/success",
        LIGDICASH_CANCEL_URL="http://localhost:5173/checkout/cancel",
        LIGDICASH_CALLBACK_URL="http://localhost:8000/api/payments/webhooks/ligdicash/",
    )
    @patch("payments.providers.ligdicash.LigdicashProvider.create_checkout")
    def test_add_product_cart_and_checkout_use_same_active_cart(self, mocked_checkout):
        mocked_checkout.return_value = CheckoutSessionResult(
            payment_url="https://app.ligdicash.com/pay/checkout/token_flow",
            session_token="token_flow",
            amount=1000,
            currency="XOF",
            order_reference="LOBEL-ORDER-1",
        )
        self.client.force_authenticate(user=self.user)

        add_response = self.client.post(
            self.order_item_url,
            {"variant_id": self.variant.id, "quantity": 2},
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)

        cart_response = self.client.get(self.cart_url)
        self.assertEqual(cart_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cart_response.data["items"]), 1)
        self.assertEqual(cart_response.data["cart_items"], 2)

        checkout_response = self.client.post(self.checkout_url, {}, format="json")
        self.assertEqual(checkout_response.status_code, status.HTTP_201_CREATED)

    @override_settings(
        PAYMENT_PROVIDER="ligdicash",
        LIGDICASH_API_KEY="test-api-key",
        LIGDICASH_API_TOKEN="test-api-token",
        LIGDICASH_BASE_URL="https://app.ligdicash.com",
        LIGDICASH_STORE_NAME="LobelStore",
        LIGDICASH_STORE_URL="http://localhost:5173",
        LIGDICASH_RETURN_URL="http://localhost:5173/checkout/success",
        LIGDICASH_CANCEL_URL="http://localhost:5173/checkout/cancel",
        LIGDICASH_CALLBACK_URL="http://localhost:8000/api/payments/webhooks/ligdicash/",
    )
    @patch("payments.providers.ligdicash.LigdicashProvider.create_checkout")
    def test_checkout_fails_when_cart_is_empty(self, mocked_checkout):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.checkout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mocked_checkout.assert_not_called()
