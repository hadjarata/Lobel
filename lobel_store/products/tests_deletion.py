from django.db.models.deletion import ProtectedError
from django.test import TestCase

from orders.models import Order, OrderItem

from .models import Category, Color, Product, ProductVariant, Size


class VariantAttributeDeletionTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Vêtements")
        self.product = Product.objects.create(
            name="T-shirt",
            category=category,
            price="10000.00",
        )

    def test_used_color_cannot_be_deleted(self):
        color = Color.objects.create(name="Noir")
        ProductVariant.objects.create(product=self.product, color=color, stock=1)

        with self.assertRaises(ProtectedError):
            color.delete()

        self.assertTrue(Color.objects.filter(pk=color.pk).exists())

    def test_used_size_cannot_be_deleted(self):
        size = Size.objects.create(name="M")
        ProductVariant.objects.create(product=self.product, size=size, stock=1)

        with self.assertRaises(ProtectedError):
            size.delete()

        self.assertTrue(Size.objects.filter(pk=size.pk).exists())

    def test_unused_attributes_can_be_deleted(self):
        color = Color.objects.create(name="Rouge")
        size = Size.objects.create(name="L")

        color.delete()
        size.delete()

        self.assertFalse(Color.objects.filter(pk=color.pk).exists())
        self.assertFalse(Size.objects.filter(pk=size.pk).exists())

    def test_product_deletion_keeps_order_history(self):
        variant = ProductVariant.objects.create(product=self.product, stock=1)
        order = Order.objects.create()
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            variant=variant,
            quantity=1,
        )

        self.product.delete()

        item.refresh_from_db()
        self.assertIsNone(item.product_id)
        self.assertIsNone(item.variant_id)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())

    def test_category_can_be_deleted_after_its_products(self):
        category = self.product.category

        self.product.delete()
        category.delete()

        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
