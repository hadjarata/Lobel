from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from .models import Category, Color, Product, ProductMedia, ProductVariant, Size


class ProductQueryCountTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Queries")
        self.color = Color.objects.create(name="Noir")
        self.size = Size.objects.create(name="M")
        self.client = APIClient()

    def create_product(self, index):
        product = Product.objects.create(
            name=f"Query {index}", category=self.category, price=10
        )
        ProductVariant.objects.create(
            product=product, color=self.color, size=self.size, stock=2
        )
        ProductMedia.objects.create(
            product=product, media_type="image", file=f"existing/{index}.png"
        )
        return product

    def query_count(self, url):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, response.data)
        return len(captured)

    def test_product_list_query_count_is_stable(self):
        self.create_product(0)
        one = self.query_count("/api/products/products/")
        for index in range(1, 10):
            self.create_product(index)
        ten = self.query_count("/api/products/products/")
        self.assertLessEqual(ten, one + 1)
        self.assertLessEqual(ten, 6)

    def test_product_detail_query_count_does_not_depend_on_related_count(self):
        product = self.create_product(0)
        one = self.query_count(f"/api/products/products/{product.pk}/")
        for index in range(1, 6):
            ProductVariant.objects.create(
                product=product, color=Color.objects.create(name=f"Detail {index}"), stock=index
            )
            ProductMedia.objects.create(
                product=product, media_type="image", file=f"existing/detail-{index}.png"
            )
        many = self.query_count(f"/api/products/products/{product.pk}/")
        self.assertLessEqual(many, one)
        self.assertLessEqual(many, 4)

    def test_media_list_query_count_is_constant(self):
        product = self.create_product(0)
        one = self.query_count("/api/products/media/")
        for index in range(1, 10):
            ProductMedia.objects.create(
                product=product, media_type="image", file=f"existing/media-{index}.png"
            )
        ten = self.query_count("/api/products/media/")
        self.assertLessEqual(ten, one)
