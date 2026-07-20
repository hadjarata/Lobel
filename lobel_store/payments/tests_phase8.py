from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from unittest.mock import patch

from orders.models import Order, OrderItem
from payments.models import Payment, PaymentAuditEvent
from payments.providers.base import (
    CheckoutSessionResult, PaymentProvider, PaymentVerificationResult,
)
from payments.services.payment_lifecycle_service import (
    PaymentLifecycleError, PaymentLifecycleService,
)
from products.models import Category, Product, ProductVariant
from users.models import Customer


class FakeLigdiCash(PaymentProvider):
    provider_name = "ligdicash"

    def __init__(self, status="pending", url="https://app.ligdicash.com/pay/session"):
        self.status = status
        self.url = url
        self.context = None

    def create_checkout(self, context):
        self.context = context
        return CheckoutSessionResult(
            payment_url=self.url, session_token="stored-creation-token",
            amount=context.amount, currency=context.currency,
            order_reference=context.order_reference,
        )

    def verify_payment(self, session_token, *, payment=None):
        return PaymentVerificationResult(
            status=self.status, response_code="00", provider="ligdicash",
            external_transaction_id="REQ-1",
            provider_reference=payment.order_reference,
            verified_amount=payment.amount, verified_currency=payment.currency,
            verification_implemented=True,
        )

    def parse_webhook(self, raw_body, content_type):
        return {}

    def extract_payment_id(self, payload):
        return None

    def build_deduplication_key(self, payload, payload_hash):
        return payload_hash


@override_settings(
    LIGDICASH_ALLOWED_CHECKOUT_HOSTS=["app.ligdicash.com"],
    LIGDICASH_HTTP_TIMEOUT=15,
    LIGDICASH_VERIFY_TLS=True,
)
class Phase8PaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("payer@example.com", password="password123")
        self.customer = Customer.objects.create(user=self.user)
        category = Category.objects.create(name="Payment")
        product = Product.objects.create(name="Article", category=category, price="5000")
        self.variant = ProductVariant.objects.create(product=product, stock=3, price="5000")
        self.order = Order.objects.create(
            customer=self.customer, status=Order.STATUS_PENDING_PAYMENT,
            snapshot_at="2026-01-01T00:00:00Z", customer_name="Client",
            customer_email="payer@example.com", delivery_recipient_name="Client Test",
            delivery_phone="+22370000000", delivery_address="Bamako",
            delivery_country="ML", subtotal_amount="5000", shipping_amount="0",
            discount_amount="0", total_amount="5000", currency="XOF",
        )
        OrderItem.objects.create(
            order=self.order, product=product, variant=self.variant, quantity=1,
            product_name="Article", unit_price="5000", subtotal="5000", currency="XOF",
        )
        self.provider = FakeLigdiCash()
        self.service = PaymentLifecycleService(provider=self.provider)

    def test_initialization_uses_only_frozen_order_amount(self):
        payment, replayed = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="key-one"
        )
        self.assertFalse(replayed)
        self.assertEqual(payment.amount, Decimal("5000"))
        self.assertEqual(self.provider.context.amount, 5000)
        self.assertEqual(payment.status, "redirect_required")
        self.assertTrue(payment.merchant_reference.startswith("LOBEL-"))

    def test_same_key_and_active_payment_are_reused(self):
        first, _ = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="same"
        )
        second, replayed = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="same"
        )
        third, active_replayed = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="other"
        )
        self.assertTrue(replayed)
        self.assertTrue(active_replayed)
        self.assertEqual({first.id, second.id, third.id}, {first.id})
        self.assertEqual(Payment.objects.count(), 1)

    def test_cross_user_and_non_payable_order_are_refused(self):
        other = User.objects.create_user("other@example.com", password="password123")
        Customer.objects.create(user=other)
        with self.assertRaises(PaymentLifecycleError) as error:
            self.service.initialize(user=other, order_id=self.order.id, idempotency_key="x")
        self.assertEqual(error.exception.code, "order_not_found")
        self.order.refresh_from_db()
        self.order.status = Order.STATUS_CANCELLED
        self.order._status_transition_allowed = True
        self.order.save(update_fields=["status"])
        with self.assertRaises(PaymentLifecycleError) as error:
            self.service.initialize(user=self.user, order_id=self.order.id, idempotency_key="y")
        self.assertEqual(error.exception.code, "order_not_payable")

    def test_invalid_checkout_urls_are_refused(self):
        for url in (
            "javascript:alert(1)", "//app.ligdicash.com/pay",
            "https://evil.example/pay", "https://user:pass@app.ligdicash.com/pay",
        ):
            with self.subTest(url=url):
                service = PaymentLifecycleService(provider=FakeLigdiCash(url=url))
                with self.assertRaises(Exception):
                    service.initialize(
                        user=self.user, order_id=self.order.id,
                        idempotency_key=f"key-{len(url)}",
                    )
                Payment.objects.all().update(status="failed")

    def test_completed_confirmation_pays_order_once_and_consumes_stock_once(self):
        payment, _ = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="complete"
        )
        complete = PaymentLifecycleService(provider=FakeLigdiCash(status="completed"))
        complete.refresh(payment_id=payment.id, user=self.user)
        complete.refresh(payment_id=payment.id, user=self.user)
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(self.variant.stock, 2)
        self.assertEqual(payment.audit_events.filter(event_type="payment_confirmed").count(), 1)

    def test_pending_confirmation_never_marks_order_paid(self):
        payment, _ = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="pending"
        )
        payment = self.service.refresh(payment_id=payment.id, user=self.user)
        self.order.refresh_from_db()
        self.assertEqual(payment.status, "processing")
        self.assertEqual(self.order.status, Order.STATUS_PAYMENT_PROCESSING)

    def test_audit_events_are_created(self):
        payment, _ = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="audit"
        )
        self.assertEqual(
            list(PaymentAuditEvent.objects.filter(payment=payment).values_list(
                "event_type", flat=True
            )),
            ["initialization_requested", "initialization_succeeded"],
        )

    def test_public_serializer_does_not_expose_provider_token_or_payload(self):
        payment, _ = self.service.initialize(
            user=self.user, order_id=self.order.id, idempotency_key="public"
        )
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get(f"/api/payments/payments/{payment.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("session_token", response.data)
        self.assertNotIn("provider_payload", response.data)

    @patch(
        "payments.services.payment_lifecycle_service.get_payment_provider",
        return_value=FakeLigdiCash(),
    )
    def test_initialize_api_accepts_only_order_and_server_amount(self, _provider):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(
            "/api/payments/checkout/",
            {"order_id": self.order.id, "amount": "1", "currency": "EUR"},
            format="json", HTTP_IDEMPOTENCY_KEY="api-key",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["amount"], Decimal("5000"))
        self.assertEqual(response.data["currency"], "XOF")
        self.assertNotIn("session_token", response.data)

    def test_initialize_api_requires_authentication_and_key(self):
        client = APIClient()
        response = client.post(
            "/api/payments/checkout/", {"order_id": self.order.id}, format="json"
        )
        self.assertEqual(response.status_code, 401)
        client.force_authenticate(self.user)
        response = client.post(
            "/api/payments/checkout/", {"order_id": self.order.id}, format="json"
        )
        self.assertEqual(response.status_code, 400)
