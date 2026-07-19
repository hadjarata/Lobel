from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Collection, Color, Product, ProductVariant


class ProductSearchTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Chaussures")
        self.product = Product.objects.create(name="Botte Azure", category=category, price=20)
        collection = Collection.objects.create(name="Été", image="existing.png")
        self.product.collections.add(collection)
        ProductVariant.objects.create(product=self.product, sku="SKU-UNIQUE", stock=2)
        self.archived = Product.objects.create(
            name="Botte cachée", category=category, price=10, is_active=False
        )
        self.client = APIClient()

    def names(self, term):
        response = self.client.get("/api/products/products/", {"search": term})
        self.assertEqual(response.status_code, 200, response.data)
        return [item["name"] for item in response.data["results"]]

    def test_search_name_case_category_collection_and_sku(self):
        for term in ("azure", "AZURE", "Chauss", "Été", "SKU-UNIQUE"):
            with self.subTest(term=term):
                self.assertEqual(self.names(term), ["Botte Azure"])

    def test_empty_none_too_long_and_hidden_product(self):
        self.assertEqual(self.names("absent"), [])
        self.assertNotIn("Botte cachée", self.names(""))
        self.assertEqual(
            self.client.get("/api/products/products/", {"search": "x" * 101}).status_code,
            400,
        )

    def test_multiple_variant_matches_do_not_duplicate_product(self):
        ProductVariant.objects.create(
            product=self.product, color=Color.objects.create(name="Distinct"),
            sku="SKU-UNIQUE-2", stock=1,
        )
        self.assertEqual(self.names("SKU-UNIQUE"), ["Botte Azure"])
