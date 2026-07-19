from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from orders.admin import OrderAdmin, OrderStatusHistoryAdmin
from orders.models import (
    CommercialDataDeletionError, Order, OrderItem, OrderStatusHistory,
)
from payments.models import Payment
from products.models import Category, Product, ProductVariant
from users.models import Customer


class CommercialOrderDeletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("retention@example.com")
        self.staff = User.objects.create_user(
            "retention-staff@example.com", is_staff=True, is_superuser=True
        )
        self.customer = Customer.objects.create(user=self.user)
        category = Category.objects.create(name="Retention")
        product = Product.objects.create(
            name="Proof", category=category, price=Decimal("100.00")
        )
        variant = ProductVariant.objects.create(product=product, stock=2)
        self.order = Order.objects.create(customer=self.customer)
        self.item = OrderItem.objects.create(
            order=self.order, product=product, variant=variant, quantity=1
        )
        self.payment = Payment.objects.create(
            order=self.order, amount=Decimal("100.00"),
            payment_method="manual", currency="XOF",
        )
        self.history = OrderStatusHistory.objects.create(
            order=self.order, from_status="", to_status=Order.STATUS_CART,
            reason_code="test_fixture",
        )

    def test_order_api_delete_is_not_supported_for_owner_and_staff(self):
        client = APIClient()
        for actor in (self.user, self.staff):
            client.force_authenticate(actor)
            response = client.delete(reverse("order-detail", args=[self.order.pk]))
            self.assertEqual(response.status_code, 405)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())
        self.assertTrue(OrderItem.objects.filter(pk=self.item.pk).exists())
        self.assertTrue(Payment.objects.filter(pk=self.payment.pk).exists())
        self.assertTrue(OrderStatusHistory.objects.filter(pk=self.history.pk).exists())

    def test_model_and_queryset_delete_are_blocked(self):
        with self.assertRaises(CommercialDataDeletionError):
            self.order.delete()
        with self.assertRaises(CommercialDataDeletionError):
            Order.objects.filter(pk=self.order.pk).delete()
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_customer_deletion_preserves_sale_and_payment(self):
        self.customer.delete()
        self.order.refresh_from_db()
        self.assertIsNone(self.order.customer_id)
        self.assertTrue(Payment.objects.filter(pk=self.payment.pk).exists())
        self.assertTrue(OrderItem.objects.filter(pk=self.item.pk).exists())

    def test_commercial_admins_never_offer_deletion(self):
        request = RequestFactory().get("/admin/")
        request.user = self.staff
        order_admin = OrderAdmin(Order, admin.site)
        history_admin = OrderStatusHistoryAdmin(OrderStatusHistory, admin.site)
        self.assertFalse(order_admin.has_delete_permission(request, self.order))
        self.assertNotIn("delete_selected", order_admin.get_actions(request))
        self.assertFalse(history_admin.has_delete_permission(request, self.history))
        self.assertFalse(history_admin.has_change_permission(request, self.history))
