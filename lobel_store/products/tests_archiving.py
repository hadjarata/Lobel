from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from payments.models import Payment
from products.models import Category, Product, ProductVariant
from products.services import CatalogueArchiveService
from users.models import Customer


class CatalogueArchivingTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("catalogue-staff@example.com", is_staff=True)
        self.customer = Customer.objects.create(
            user=User.objects.create_user("catalogue-owner@example.com")
        )
        self.category = Category.objects.create(name="Archive")
        self.product = Product.objects.create(
            name="Archived dress", category=self.category, price=Decimal("100.00")
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=5)
        self.order = Order.objects.create(customer=self.customer)
        self.item = OrderItem.objects.create(
            order=self.order, product=self.product, variant=self.variant, quantity=1
        )
        self.payment = Payment.objects.create(
            order=self.order, amount=Decimal("100.00"),
            payment_method="manual", currency="XOF",
        )

    def test_category_with_products_is_protected_from_physical_delete(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_archived_category_and_product_are_hidden_but_history_remains(self):
        service = CatalogueArchiveService()
        service.archive_category(self.category)
        service.archive_product(self.product)
        self.product.refresh_from_db()
        self.variant.refresh_from_db()
        public = APIClient()
        response = public.get(reverse("product-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertFalse(self.product.is_active)
        self.assertFalse(self.variant.is_active)
        self.assertTrue(OrderItem.objects.filter(pk=self.item.pk).exists())
        self.assertTrue(Payment.objects.filter(pk=self.payment.pk).exists())

    def test_archived_variant_cannot_be_added_to_cart(self):
        CatalogueArchiveService().archive_variant(self.variant)
        client = APIClient()
        client.force_authenticate(self.customer.user)
        response = client.post(
            reverse("orderitem-list"),
            {"variant_id": self.variant.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_catalogue_delete_api_is_replaced_by_explicit_archive_action(self):
        client = APIClient()
        client.force_authenticate(self.staff)
        delete = client.delete(reverse("product-detail", args=[self.product.pk]))
        self.assertEqual(delete.status_code, 405)
        archive = client.post(reverse("product-archive", args=[self.product.pk]))
        self.assertEqual(archive.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)
