from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from .models import Category, Product, ProductMedia, ProductVariant
from .querysets import product_queryset
from .serializers import ProductListSerializer


class ProductSerializerPerformanceTests(TestCase):
    def test_prefetched_serializer_performs_no_queries(self):
        category = Category.objects.create(name="Serializer")
        for index in range(5):
            product = Product.objects.create(name=f"P{index}", category=category, price=1)
            ProductVariant.objects.create(product=product, stock=1)
            ProductMedia.objects.create(
                product=product, media_type="image", file=f"existing/{index}.png"
            )
        products = list(product_queryset(public=True, detail=False).order_by("id"))
        with CaptureQueriesContext(connection) as captured:
            data = ProductListSerializer(products, many=True).data
        self.assertEqual(len(data), 5)
        self.assertEqual(len(captured), 0)
