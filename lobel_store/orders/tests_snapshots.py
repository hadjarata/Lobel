from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from orders.services.cart_service import CartService
from orders.services.snapshot_service import FinancialSnapshotService
from payments.models import Payment
from payments.providers.mock import MockProvider
from payments.services.checkout_service import CheckoutService
from payments.services.payment_service import PaymentProcessingError, PaymentService
from products.models import Category, Color, Product, ProductVariant, Size
from users.models import Customer


@override_settings(DEBUG=True, PAYMENT_PROVIDER="mock", FRONTEND_URL="http://testserver")
class ImmutableOrderSnapshotTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "snapshot@example.com", email="snapshot@example.com",
            first_name="Awa", last_name="Diallo",
        )
        self.customer = Customer.objects.create(
            user=self.user, phone_number="+22370000000",
            address="Hamdallaye ACI 2000", country="ML",
        )
        category = Category.objects.create(name="Mode")
        self.product = Product.objects.create(
            name="Robe historique", category=category, price=Decimal("1250.25")
        )
        self.color = Color.objects.create(name="Noir")
        self.size = Size.objects.create(name="M")
        self.variant = ProductVariant.objects.create(
            product=self.product, color=self.color, size=self.size,
            stock=10, sku="ROB-N-M", price=Decimal("1200.10"),
        )
        self.item, _ = CartService().add_variant(
            customer=self.customer, variant=self.variant, quantity=2
        )
        result = CheckoutService(payment_provider=MockProvider()).create_checkout_session(
            self.user
        )
        self.payment = Payment.objects.get(pk=result["paymentId"])
        self.order = Order.objects.get(pk=self.item.order_id)
        self.item.refresh_from_db()

    def test_checkout_freezes_line_customer_and_totals(self):
        self.assertEqual(self.item.product_reference, self.product.id)
        self.assertEqual(self.item.variant_reference, self.variant.id)
        self.assertEqual(self.item.variant_name, "Noir / M")
        self.assertEqual(self.item.unit_price, Decimal("1200.10"))
        self.assertEqual(self.item.discount_amount, Decimal("0.00"))
        self.assertEqual(self.item.subtotal, Decimal("2400.20"))
        self.assertEqual(self.item.currency, "XOF")
        self.assertEqual(self.order.customer_name, "Awa Diallo")
        self.assertEqual(self.order.delivery_phone, "+22370000000")
        self.assertEqual(self.order.delivery_address, "Hamdallaye ACI 2000")
        self.assertEqual(self.order.subtotal_amount, Decimal("2400.20"))
        self.assertEqual(self.order.total_amount, Decimal("2400.20"))
        self.assertEqual(self.payment.amount, self.order.total_amount)
        self.assertEqual(self.payment.currency, self.order.currency)

    def test_catalogue_and_profile_changes_do_not_change_serialized_history(self):
        before = OrderSerializer(self.order).data
        self.product.name = "Nom modifié"
        self.product.price = Decimal("9999.00")
        self.product.save(update_fields=["name", "price"])
        self.variant.sku = "NEW-SKU"
        self.variant.price = Decimal("8888.00")
        self.variant.is_active = False
        self.variant.save(update_fields=["sku", "price", "is_active"])
        self.color.name = "Rouge"
        self.color.save(update_fields=["name"])
        self.size.name = "XL"
        self.size.save(update_fields=["name"])
        self.customer.address = "Nouvelle adresse"
        self.customer.phone_number = "+22371111111"
        self.customer.save(update_fields=["address", "phone_number"])
        self.order.refresh_from_db()
        after = OrderSerializer(self.order).data
        for field in (
            "customer_name", "customer_email", "delivery_phone",
            "delivery_address", "subtotal_amount", "total_amount", "currency",
        ):
            self.assertEqual(after[field], before[field])
        self.assertEqual(after["items"], before["items"])

    def test_physical_catalogue_deletion_preserves_history(self):
        expected = OrderSerializer(self.order).data["items"][0]
        self.product.delete()
        self.item.refresh_from_db()
        self.assertIsNone(self.item.product_id)
        self.assertIsNone(self.item.variant_id)
        current = OrderSerializer(Order.objects.get(pk=self.order.pk)).data["items"][0]
        self.assertEqual(current["product_name"], expected["product_name"])
        self.assertEqual(current["variant_name"], expected["variant_name"])
        self.assertEqual(current["subtotal"], expected["subtotal"])

    def test_model_and_api_reject_changes_after_snapshot(self):
        self.item.quantity = 3
        with self.assertRaises(ValidationError):
            self.item.save()
        self.order.total_amount = Decimal("1.00")
        with self.assertRaises(ValidationError):
            self.order.save()
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.patch(
            reverse("orderitem-detail", args=[self.item.pk]),
            {"quantity": 3}, format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_payment_processing_checks_frozen_total(self):
        self.payment.amount = Decimal("1.00")
        self.payment.save(update_fields=["amount"])
        with self.assertRaises(PaymentProcessingError):
            PaymentService().handle_payment_completed(self.payment)


class FinancialSnapshotFormulaTests(TestCase):
    def test_decimal_line_and_order_formulas(self):
        line = FinancialSnapshotService.line_subtotal(
            unit_price=Decimal("10.15"), quantity=3,
            discount_amount=Decimal("0.10"),
        )
        self.assertIsInstance(line, Decimal)
        self.assertEqual(line, Decimal("30.35"))
        total = FinancialSnapshotService.order_total(
            subtotal=line, shipping_amount=Decimal("2.50"),
            discount_amount=Decimal("1.00"),
        )
        self.assertEqual(total, Decimal("31.85"))

    def test_discount_cannot_exceed_gross_amount(self):
        with self.assertRaises(ValidationError):
            FinancialSnapshotService.line_subtotal(
                unit_price=Decimal("10.00"), quantity=1,
                discount_amount=Decimal("10.01"),
            )
