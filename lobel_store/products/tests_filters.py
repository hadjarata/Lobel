from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Collection, Color, Product, ProductVariant, Size


class ProductFilterTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Filtres")
        other = Category.objects.create(name="Autre")
        self.collection = Collection.objects.create(name="Promo", image="existing.png")
        self.color = Color.objects.create(name="Rouge")
        self.size = Size.objects.create(name="M")
        self.available = Product.objects.create(name="Alpha", category=self.category, price=10)
        self.available.collections.add(self.collection)
        ProductVariant.objects.create(
            product=self.available, color=self.color, size=self.size, stock=2
        )
        self.unavailable = Product.objects.create(name="Beta", category=other, price=30)
        ProductVariant.objects.create(product=self.unavailable, stock=0)
        self.client = APIClient()

    def names(self, **params):
        response = self.client.get("/api/products/products/", params)
        self.assertEqual(response.status_code, 200, response.data)
        return [item["name"] for item in response.data["results"]]

    def test_structured_filters_and_combinations(self):
        self.assertEqual(self.names(category=self.category.pk), ["Alpha"])
        self.assertEqual(self.names(collection=self.collection.slug), ["Alpha"])
        self.assertEqual(self.names(available="true"), ["Alpha"])
        self.assertEqual(self.names(min_price=20, max_price=40), ["Beta"])
        self.assertEqual(self.names(color=self.color.pk, size=self.size.pk), ["Alpha"])

    def test_ordering_allowlist_and_stability(self):
        self.assertEqual(self.names(ordering="name"), ["Alpha", "Beta"])
        self.assertEqual(self.names(ordering="-price"), ["Beta", "Alpha"])
        self.assertEqual(
            self.client.get("/api/products/products/", {"ordering": "description"}).status_code,
            400,
        )

    def test_invalid_parameters_are_controlled(self):
        for params in (
            {"min_price": "bad"}, {"min_price": 20, "max_price": 1},
            {"available": "maybe"}, {"category": "bad"}, {"color": "bad"},
        ):
            self.assertEqual(self.client.get("/api/products/products/", params).status_code, 400)

    def test_filter_options_are_complete_and_not_paginated(self):
        response = self.client.get("/api/products/products/filter-options/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            [item["name"] for item in response.data["categories"]],
            ["Autre", "Filtres"],
        )
        self.assertEqual(response.data["collections"], [
            {"id": self.collection.pk, "name": "Promo", "slug": "promo"}
        ])
        self.assertEqual(response.data["colors"], [
            {"id": self.color.pk, "name": "Rouge", "hex_code": None}
        ])
        self.assertEqual(response.data["sizes"], [{"id": self.size.pk, "name": "M"}])
        self.assertEqual(response.data["price"], {"min": "10.00", "max": "30.00"})

    def test_filter_options_exclude_inactive_and_out_of_stock_facets(self):
        inactive_color = Color.objects.create(name="Invisible")
        inactive_size = Size.objects.create(name="XL")
        ProductVariant.objects.create(
            product=self.unavailable,
            color=inactive_color,
            size=inactive_size,
            stock=0,
        )
        response = self.client.get("/api/products/products/filter-options/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Invisible", [item["name"] for item in response.data["colors"]])
        self.assertNotIn("XL", [item["name"] for item in response.data["sizes"]])
