from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Product


class ProductPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Pagination")
        Product.objects.bulk_create([
            Product(name=f"Product {index:03}", category=category, price=index + 1)
            for index in range(125)
        ])

    def setUp(self):
        self.client = APIClient()

    def test_default_and_navigation_format(self):
        first = self.client.get("/api/products/products/")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(set(first.data), {"count", "next", "previous", "results"})
        self.assertEqual(len(first.data["results"]), 20)
        self.assertIsNotNone(first.data["next"])
        second = self.client.get("/api/products/products/?page=2")
        self.assertIsNotNone(second.data["previous"])
        self.assertFalse(
            {item["id"] for item in first.data["results"]}
            & {item["id"] for item in second.data["results"]}
        )

    def test_custom_size_is_capped_and_cannot_disable_pagination(self):
        self.assertEqual(len(self.client.get("/api/products/products/?page_size=1").data["results"]), 1)
        self.assertEqual(len(self.client.get("/api/products/products/?page_size=1000000").data["results"]), 100)
        for value in ("-1", "abc", "0"):
            self.assertEqual(
                self.client.get(f"/api/products/products/?page_size={value}").status_code,
                400,
            )

    def test_invalid_page_and_archived_exclusion(self):
        Product.objects.filter(name="Product 000").update(is_active=False)
        response = self.client.get("/api/products/products/?page=999")
        self.assertEqual(response.status_code, 404)
        listed = self.client.get("/api/products/products/?page_size=100").data["results"]
        self.assertNotIn("Product 000", [item["name"] for item in listed])
