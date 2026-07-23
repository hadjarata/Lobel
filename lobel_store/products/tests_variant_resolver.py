from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Product, ProductVariant


class VariantResolverTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Resolver")
        self.product = Product.objects.create(name="Produit", category=category, price="25.00")
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="SKU-1", stock=3, is_active=True
        )
        self.client = APIClient()
        self.url = "/api/products/products/resolve-variants/"

    def test_resolves_variants_in_one_public_request(self):
        response = self.client.post(self.url, {"variant_ids": [self.variant.id]}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["results"][0]["sku"], "SKU-1")
        self.assertEqual(response.data["results"][0]["price"], "25.00")
        self.assertTrue(response.data["results"][0]["is_available"])

    def test_reports_missing_ids(self):
        response = self.client.post(
            self.url, {"variant_ids": [self.variant.id, 999999]}, format="json"
        )
        self.assertEqual(response.data["missing_ids"], [999999])

    def test_rejects_invalid_or_oversized_input(self):
        for payload in (
            {}, {"variant_ids": []}, {"variant_ids": ["bad"]},
            {"variant_ids": list(range(1, 52))},
        ):
            self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 400)
