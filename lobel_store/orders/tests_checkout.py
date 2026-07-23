from copy import deepcopy

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import CheckoutCreationReceipt, Order, OrderItem
from products.models import Category, Product, ProductVariant
from users.models import Customer


class CheckoutApiTests(TestCase):
    base_url = "/api/orders/orders/checkout"

    def setUp(self):
        self.user = User.objects.create_user(
            username="checkout@example.com", email="checkout@example.com",
            password="password123", first_name="Awa", last_name="Traore",
        )
        self.customer = Customer.objects.create(user=self.user)
        category = Category.objects.create(name="Checkout")
        self.product = Product.objects.create(
            name="Robe", category=category, price="10000.00"
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, stock=5, price="9000.00", sku="ROBE-1"
        )
        self.cart = Order.objects.create(customer=self.customer)
        self.item = OrderItem.objects.create(
            order=self.cart, product=self.product, variant=self.variant,
            quantity=2, unit_price="9000.00",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.payload = {
            "shipping_address": {
                "recipient_name": "Awa Traore",
                "phone": "+22370000000",
                "country": "ML",
                "region": "Bamako",
                "city": "Bamako",
                "district": "Hamdallaye",
                "street": "Rue 123",
                "instructions": "Appeler à l'arrivée",
            },
            "delivery_method": "express_bamako",
            "billing_same_as_shipping": True,
        }

    def preview(self, payload=None):
        return self.client.post(
            f"{self.base_url}/preview/", payload or self.payload, format="json"
        )

    def create(self, payload, key="checkout-key-1"):
        return self.client.post(
            f"{self.base_url}/create-order/", payload, format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def test_delivery_methods_are_calculated_server_side(self):
        response = self.client.post(
            f"{self.base_url}/delivery-options/",
            {"shipping_address": self.payload["shipping_address"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["code"] for item in response.data["delivery_methods"]},
            {"standard", "express_bamako"},
        )

    def test_express_is_not_available_outside_bamako(self):
        payload = deepcopy(self.payload)
        payload["shipping_address"]["city"] = "Sikasso"
        response = self.client.post(
            f"{self.base_url}/delivery-options/",
            {"shipping_address": payload["shipping_address"]}, format="json",
        )
        self.assertEqual(
            [item["code"] for item in response.data["delivery_methods"]], ["standard"]
        )

    def test_preview_returns_authoritative_total_and_version(self):
        response = self.preview()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["amounts"]["subtotal"], "18000.00")
        self.assertEqual(response.data["amounts"]["shipping"], "1500.00")
        self.assertEqual(response.data["amounts"]["total"], "19500.00")
        self.assertEqual(len(response.data["checkout_version"]), 64)

    def test_preview_rejects_insufficient_stock_with_line_error(self):
        self.variant.stock = 1
        self.variant.save(update_fields=["stock"])
        response = self.preview()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "invalid_cart")
        self.assertEqual(response.data["errors"][0]["errors"][0]["code"], "insufficient_stock")

    def test_create_requires_version_and_idempotency_key(self):
        response = self.create(self.payload)
        self.assertEqual(response.status_code, 400)
        versioned = {**self.payload, "checkout_version": "a" * 64}
        response = self.client.post(
            f"{self.base_url}/create-order/", versioned, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "invalid_idempotency_key")

    def test_create_freezes_order_and_reserves_stock_without_creating_payment(self):
        preview = self.preview().data
        response = self.create({**self.payload, "checkout_version": preview["checkout_version"]})
        self.assertEqual(response.status_code, 201)
        self.cart.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.cart.status, Order.STATUS_PENDING_PAYMENT)
        self.assertEqual(self.cart.total_amount, 19500)
        self.assertEqual(self.cart.delivery_city, "Bamako")
        self.assertIsNotNone(self.cart.snapshot_at)
        self.assertEqual(self.variant.stock, 3)
        self.assertIsNotNone(self.cart.stock_reserved_at)
        self.assertIsNotNone(self.cart.stock_reservation_expires_at)
        self.assertIsNone(self.cart.stock_consumed_at)
        self.assertEqual(self.cart.payments.count(), 0)

    def test_same_key_replays_same_order(self):
        preview = self.preview().data
        payload = {**self.payload, "checkout_version": preview["checkout_version"]}
        first = self.create(payload)
        second = self.create(payload)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data["replayed"])
        self.assertEqual(first.data["order"]["id"], second.data["order"]["id"])
        self.assertEqual(CheckoutCreationReceipt.objects.count(), 1)

    def test_same_key_with_different_payload_is_rejected(self):
        preview = self.preview().data
        payload = {**self.payload, "checkout_version": preview["checkout_version"]}
        self.create(payload)
        changed = deepcopy(payload)
        changed["shipping_address"]["instructions"] = "Autre instruction"
        response = self.create(changed)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "idempotency_conflict")

    def test_stale_preview_is_rejected_if_stock_changes(self):
        preview = self.preview().data
        self.variant.stock = 4
        self.variant.save(update_fields=["stock"])
        response = self.create(
            {**self.payload, "checkout_version": preview["checkout_version"]}
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "stale_checkout")
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, Order.STATUS_CART)

    def test_stale_preview_is_rejected_if_price_changes(self):
        preview = self.preview().data
        self.variant.price = "9500.00"
        self.variant.save(update_fields=["price"])
        response = self.create(
            {**self.payload, "checkout_version": preview["checkout_version"]}
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "stale_checkout")

    def test_preview_warns_when_cart_snapshot_price_changed(self):
        self.variant.price = "9500.00"
        self.variant.save(update_fields=["price"])
        response = self.preview()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["warnings"][0]["code"], "price_changed")

    def test_second_key_cannot_create_a_duplicate_from_same_cart(self):
        preview = self.preview().data
        payload = {**self.payload, "checkout_version": preview["checkout_version"]}
        first = self.create(payload, key="tab-one")
        second = self.create(payload, key="tab-two")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.data["code"], "order_already_created")
        self.assertEqual(
            Order.objects.filter(
                customer=self.customer, status=Order.STATUS_PENDING_PAYMENT
            ).count(),
            1,
        )

    def test_pending_endpoint_is_owner_scoped(self):
        preview = self.preview().data
        self.create({**self.payload, "checkout_version": preview["checkout_version"]})
        response = self.client.get(f"{self.base_url}/pending/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["order"]["id"], self.cart.id)
        other = User.objects.create_user("other", password="password123")
        Customer.objects.create(user=other)
        self.client.force_authenticate(other)
        response = self.client.get(f"{self.base_url}/pending/")
        self.assertIsNone(response.data["order"])

    def test_unauthenticated_checkout_is_rejected(self):
        self.client.force_authenticate(None)
        response = self.preview()
        self.assertEqual(response.status_code, 401)
