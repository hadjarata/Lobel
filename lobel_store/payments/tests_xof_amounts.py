from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from orders.models import Order, OrderItem
from orders.services.snapshot_service import FinancialSnapshotService
from payments.models import Payment, Refund
from payments.providers.mock import MockProvider
from payments.services.refund_service import RefundError, RefundService
from products.models import Category, Product, ProductVariant
from users.models import Customer


class IntegerXOFAmountTests(TestCase):
    def setUp(self):
        user = User.objects.create_user("integer-xof@example.com")
        customer = Customer.objects.create(user=user)
        category = Category.objects.create(name="Montants XOF")
        self.product = Product.objects.create(
            name="Article entier", category=category, price=Decimal("1000.00")
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, stock=2, price=Decimal("900.00")
        )
        self.order = Order.objects.create(
            customer=customer,
            status=Order.STATUS_PAID,
            subtotal_amount=Decimal("900.00"),
            shipping_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            currency="XOF",
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            variant=self.variant,
            quantity=1,
            unit_price=Decimal("900.00"),
            discount_amount=Decimal("0.00"),
            subtotal=Decimal("900.00"),
            currency="XOF",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
            currency="XOF",
            payment_method="mock",
            provider="mock",
            status="completed",
        )

    def assert_database_rejects_fraction(self, queryset, field):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                queryset.update(**{field: Decimal("10.50")})

    def test_model_validation_rejects_fractional_catalogue_prices(self):
        self.product.price = Decimal("1000.50")
        with self.assertRaises(ValidationError):
            self.product.full_clean()
        self.variant.price = Decimal("900.50")
        with self.assertRaises(ValidationError):
            self.variant.full_clean()

    def test_database_rejects_fractional_catalogue_prices(self):
        self.assert_database_rejects_fraction(
            Product.objects.filter(pk=self.product.pk), "price"
        )
        self.assert_database_rejects_fraction(
            ProductVariant.objects.filter(pk=self.variant.pk), "price"
        )

    def test_database_rejects_every_fractional_order_amount(self):
        for field in (
            "subtotal_amount", "shipping_amount",
            "discount_amount", "total_amount",
        ):
            with self.subTest(field=field):
                self.assert_database_rejects_fraction(
                    Order.objects.filter(pk=self.order.pk), field
                )
        for field in ("unit_price", "discount_amount", "subtotal"):
            with self.subTest(field=field):
                self.assert_database_rejects_fraction(
                    OrderItem.objects.filter(pk=self.item.pk), field
                )

    def test_database_rejects_fractional_payment_and_refund(self):
        self.assert_database_rejects_fraction(
            Payment.objects.filter(pk=self.payment.pk), "amount"
        )
        refund = Refund.objects.create(
            payment=self.payment,
            order=self.order,
            amount=Decimal("100.00"),
            currency="XOF",
            reason="Test",
            idempotency_key="integer-refund",
            request_fingerprint="a" * 64,
        )
        self.assert_database_rejects_fraction(
            Refund.objects.filter(pk=refund.pk), "amount"
        )

    def test_services_and_provider_never_round_fractional_xof(self):
        with self.assertRaises(ValidationError):
            FinancialSnapshotService.money(Decimal("1000.50"))
        with self.assertRaises(ValidationError):
            MockProvider.format_amount(Decimal("1000.50"))
        with self.assertRaises(RefundError) as raised:
            RefundService(provider=MockProvider()).request(
                payment=self.payment,
                amount=Decimal("100.50"),
                reason="Fraction interdite",
                actor=None,
                idempotency_key="fraction-refund",
            )
        self.assertEqual(raised.exception.code, "invalid_amount")

    def test_integer_values_remain_accepted(self):
        self.assertEqual(
            FinancialSnapshotService.money(Decimal("1000.00")),
            Decimal("1000.00"),
        )
        self.assertEqual(MockProvider.format_amount(Decimal("1000.00")), 1000)
