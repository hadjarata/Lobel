from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from products.models import Category, Product, ProductVariant
from users.models import Customer
from .models import CartMergeReceipt, Order, OrderItem


class CartMergeApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="merge@example.com", email="merge@example.com", password="Password123!"
        )
        self.customer = Customer.objects.create(user=self.user)
        category = Category.objects.create(name="Fusion")
        self.product = Product.objects.create(name="Robe", category=category, price="1000.00")
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="ROB-M", stock=5, is_active=True
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = "/api/orders/orders/cart/merge/"

    def merge(self, items, key="guest-key"):
        return self.client.post(
            self.url, {"items": items}, format="json", HTTP_IDEMPOTENCY_KEY=key
        )

    def test_merge_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.merge([{"variant_id": self.variant.id, "quantity": 1}]).status_code, 401)

    def test_merge_requires_idempotency_key(self):
        response = self.client.post(
            self.url, {"items": [{"variant_id": self.variant.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "invalid_idempotency_key")

    def test_merge_creates_cart_and_line(self):
        response = self.merge([{"variant_id": self.variant.id, "quantity": 2}])
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["cart"]["cart_items"], 2)
        self.assertEqual(response.data["merged_items"][0]["accepted_quantity"], 2)

    def test_merge_adds_to_existing_variant(self):
        cart = Order.objects.create(customer=self.customer)
        OrderItem.objects.create(order=cart, variant=self.variant, product=self.product, quantity=1)
        response = self.merge([{"variant_id": self.variant.id, "quantity": 2}])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart"]["cart_items"], 3)

    def test_merge_deduplicates_request_items(self):
        response = self.merge([
            {"variant_id": self.variant.id, "quantity": 1},
            {"variant_id": self.variant.id, "quantity": 2},
        ])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart"]["cart_items"], 3)

    def test_merge_adjusts_to_stock(self):
        response = self.merge([{"variant_id": self.variant.id, "quantity": 9}])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["adjusted_items"][0]["accepted_quantity"], 5)

    def test_merge_partially_rejects_missing_variant(self):
        response = self.merge([
            {"variant_id": self.variant.id, "quantity": 1},
            {"variant_id": 999999, "quantity": 1},
        ])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart"]["cart_items"], 1)
        self.assertEqual(response.data["rejected_items"][0]["code"], "invalid_variant")

    def test_merge_rejects_inactive_variant(self):
        self.variant.is_active = False
        self.variant.save(update_fields=["is_active"])
        response = self.merge([{"variant_id": self.variant.id, "quantity": 1}])
        self.assertEqual(response.data["rejected_items"][0]["code"], "inactive_variant")

    def test_merge_rejects_inactive_product(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])
        response = self.merge([{"variant_id": self.variant.id, "quantity": 1}])
        self.assertEqual(response.data["rejected_items"][0]["code"], "inactive_product")

    def test_merge_is_idempotent(self):
        items = [{"variant_id": self.variant.id, "quantity": 2}]
        first = self.merge(items)
        second = self.merge(items)
        self.assertFalse(first.data["replayed"])
        self.assertTrue(second.data["replayed"])
        self.assertEqual(second.data["cart"]["cart_items"], 2)
        self.assertEqual(CartMergeReceipt.objects.count(), 1)

    def test_key_reuse_with_different_payload_conflicts(self):
        self.merge([{"variant_id": self.variant.id, "quantity": 1}])
        response = self.merge([{"variant_id": self.variant.id, "quantity": 2}])
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "idempotency_conflict")

    def test_prices_and_totals_from_client_are_ignored(self):
        response = self.client.post(
            self.url,
            {"items": [{"variant_id": self.variant.id, "quantity": 1, "price": "0", "total": "0"}]},
            format="json", HTTP_IDEMPOTENCY_KEY="ignore-money",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart"]["items"][0]["unit_price"], "1000.00")

    def test_clear_cart_is_atomic_endpoint(self):
        self.merge([{"variant_id": self.variant.id, "quantity": 1}])
        response = self.client.delete("/api/orders/orders/cart/clear/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart_items"], 0)
        self.assertFalse(OrderItem.objects.exists())

