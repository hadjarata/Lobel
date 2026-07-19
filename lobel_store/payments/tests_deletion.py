from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import CommercialDataDeletionError, Order
from payments.admin import PaymentAdmin
from payments.models import Payment
from users.models import Customer


class PaymentRetentionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("payment-retention@example.com")
        customer = Customer.objects.create(user=self.user)
        self.order = Order.objects.create(customer=customer)
        self.payment = Payment.objects.create(
            order=self.order, amount=Decimal("50.00"),
            payment_method="manual", status="failed", currency="XOF",
        )

    def test_payment_api_delete_is_not_supported(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.delete(reverse("payment-detail", args=[self.payment.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Payment.objects.filter(pk=self.payment.pk).exists())

    def test_direct_and_queryset_payment_deletion_are_blocked(self):
        with self.assertRaises(CommercialDataDeletionError):
            self.payment.delete()
        with self.assertRaises(CommercialDataDeletionError):
            Payment.objects.filter(pk=self.payment.pk).delete()

    def test_payment_protects_its_order_at_database_relation_level(self):
        # The model guard blocks first; the PROTECT relation is the final
        # schema-level defense for controlled collector operations.
        field = Payment._meta.get_field("order")
        self.assertEqual(field.remote_field.on_delete.__name__, "PROTECT")

    def test_payment_admin_is_read_only_and_non_deletable(self):
        staff = User.objects.create_superuser(
            "payment-admin@example.com", password="x"
        )
        request = RequestFactory().get("/admin/")
        request.user = staff
        model_admin = PaymentAdmin(Payment, admin.site)
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request, self.payment))
        self.assertFalse(model_admin.has_delete_permission(request, self.payment))
        self.assertNotIn("delete_selected", model_admin.get_actions(request))
