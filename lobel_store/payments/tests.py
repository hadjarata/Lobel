import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem
from orders.services.order_service import InsufficientStockError, OrderService
from payments.models import Payment, PaymentWebhookEvent
from payments.providers.base import (
    CheckoutSessionResult,
    PaymentCommunicationError,
    PaymentInvalidResponseError,
    PaymentVerificationResult,
)
from payments.services.payment_service import PaymentService
from products.models import Category, Product, ProductVariant
from users.models import Customer


LIGDICASH_SETTINGS = {
    "PAYMENT_PROVIDER": "ligdicash",
    "LIGDICASH_API_KEY": "test-api-key",
    "LIGDICASH_API_TOKEN": "test-api-token",
    "LIGDICASH_BASE_URL": "https://app.ligdicash.com",
    "LIGDICASH_STORE_NAME": "LobelStore",
    "LIGDICASH_STORE_URL": "http://localhost:5173",
    "LIGDICASH_RETURN_URL": "http://localhost:5173/checkout/success",
    "LIGDICASH_CANCEL_URL": "http://localhost:5173/checkout/cancel",
    "LIGDICASH_CALLBACK_URL": "http://localhost:8000/api/payments/webhooks/ligdicash/",
}


@override_settings(**LIGDICASH_SETTINGS)
class CheckoutViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="checkout@example.com",
            email="checkout@example.com",
            password="password123",
            first_name="Awa",
            last_name="Diallo",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Shoes")
        self.product = Product.objects.create(
            name="Runner",
            category=self.category,
            price="500.00",
        )
        self.url = reverse("payment-checkout")

    def _create_cart(self, quantity=2):
        order = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=order, product=self.product, quantity=quantity)
        return order

    @patch("payments.providers.ligdicash.LigdicashProvider.create_checkout")
    def test_checkout_creates_pending_payment_and_returns_payment_url(self, mocked_checkout):
        order = self._create_cart()
        mocked_checkout.return_value = CheckoutSessionResult(
            payment_url="https://app.ligdicash.com/pay/checkout/token123",
            session_token="token123",
            amount=1000,
            currency="XOF",
            order_reference=f"LOBEL-ORDER-{order.id}",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["payment_url"], mocked_checkout.return_value.payment_url)
        self.assertEqual(response.data["sessionToken"], "token123")
        self.assertEqual(response.data["orderId"], order.id)

        payment = Payment.objects.get(id=response.data["paymentId"])
        self.assertEqual(payment.order, order)
        self.assertEqual(payment.provider, "ligdicash")
        self.assertEqual(payment.payment_method, "ligdicash")
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.session_token, "token123")
        self.assertEqual(payment.order_reference, f"LOBEL-ORDER-{order.id}")

    @patch("payments.providers.ligdicash.LigdicashProvider.create_checkout")
    def test_payment_serializer_exposes_processed_at(self, mocked_checkout):
        order = self._create_cart()
        mocked_checkout.return_value = CheckoutSessionResult(
            payment_url="https://app.ligdicash.com/pay/checkout/token456",
            session_token="token456",
            amount=1000,
            currency="XOF",
            order_reference=f"LOBEL-ORDER-{order.id}",
        )
        self.client.force_authenticate(user=self.user)
        checkout_response = self.client.post(self.url, {}, format="json")
        payment_id = checkout_response.data["paymentId"]

        detail_response = self.client.get(reverse("payment-detail", args=[payment_id]))

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIn("processed_at", detail_response.data)
        self.assertIsNone(detail_response.data["processed_at"])

    def test_checkout_requires_authentication(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checkout_rejects_empty_cart(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Le panier est vide.")
        self.assertFalse(Payment.objects.exists())

    @patch("payments.providers.ligdicash.LigdicashProvider.create_checkout")
    def test_checkout_returns_bad_gateway_when_provider_communication_fails(self, mocked_checkout):
        self._create_cart()
        mocked_checkout.side_effect = PaymentCommunicationError("Impossible de contacter LigdiCash.")
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        payment = Payment.objects.get()
        self.assertEqual(payment.status, "failed")
        self.assertIsNone(payment.session_token)

    @patch("payments.providers.ligdicash.LigdicashProvider.create_checkout")
    def test_checkout_returns_bad_gateway_when_provider_response_is_invalid(self, mocked_checkout):
        self._create_cart()
        mocked_checkout.side_effect = PaymentInvalidResponseError("Réponse LigdiCash invalide.")
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        payment = Payment.objects.get()
        self.assertEqual(payment.status, "failed")
        self.assertIsNone(payment.session_token)


@override_settings(**LIGDICASH_SETTINGS)
class PaymentWebhookViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="webhook@example.com",
            email="webhook@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Accessories")
        self.product = Product.objects.create(
            name="Cap",
            category=self.category,
            price="300.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=10)
        self.order = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)
        self.payment = Payment.objects.create(
            order=self.order,
            amount="300.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="pending",
            session_token="ligdi_token_123",
            order_reference=f"LOBEL-ORDER-{self.order.id}",
            currency="XOF",
        )
        self.url = reverse("payment-webhook")

    def _webhook_payload(self, **overrides):
        payload = {
            "response_code": "00",
            "status": "completed",
            "amount": 300,
            "request_id": "LIGDI-REQ-123",
            "custom_data": [
                {
                    "keyof_customdata": "payment_id",
                    "valueof_customdata": str(self.payment.id),
                },
                {
                    "keyof_customdata": "transaction_id",
                    "valueof_customdata": f"LOBEL-PAYMENT-{self.payment.id}",
                },
            ],
        }
        payload.update(overrides)
        return payload

    def _post_webhook(self, payload):
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return self.client.post(
            self.url,
            data=raw_body,
            content_type="application/json",
        )

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_completed_webhook_fulfills_order(self, mocked_verify):
        mocked_verify.return_value = PaymentVerificationResult(
            status="completed",
            response_code="00",
            external_transaction_id="LIGDI-REQ-123",
        )

        response = self._post_webhook(self._webhook_payload())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.variant.refresh_from_db()

        self.assertEqual(self.payment.status, "completed")
        self.assertEqual(self.payment.external_transaction_id, "LIGDI-REQ-123")
        self.assertIsNotNone(self.payment.processed_at)
        self.assertTrue(self.order.complete)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(self.variant.stock, 9)

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_failed_webhook_updates_payment_status(self, mocked_verify):
        mocked_verify.return_value = PaymentVerificationResult(
            status="notcompleted",
            response_code="00",
            external_transaction_id="LIGDI-REQ-FAILED",
        )

        response = self._post_webhook(self._webhook_payload(status="notcompleted"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "failed")
        self.assertEqual(self.payment.external_transaction_id, "LIGDI-REQ-FAILED")

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_completed_webhook_is_idempotent(self, mocked_verify):
        self.payment.status = "completed"
        self.payment.external_transaction_id = "LIGDI-REQ-ORIGINAL"
        self.payment.processed_at = timezone.now()
        self.payment.save(update_fields=["status", "external_transaction_id", "processed_at"])
        self.order.status = Order.STATUS_PAID
        self.order.complete = True
        self.order.paid_at = timezone.now()
        self.order.save(update_fields=["status", "complete", "paid_at"])
        initial_stock = self.variant.stock

        response = self._post_webhook(self._webhook_payload(request_id="LIGDI-REQ-RETRY"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.payment.external_transaction_id, "LIGDI-REQ-ORIGINAL")
        self.assertEqual(self.variant.stock, initial_stock)
        mocked_verify.assert_not_called()

    def test_unknown_payment_id_is_consumed_with_200(self):
        payload = self._webhook_payload()
        payload["custom_data"] = [
            {
                "keyof_customdata": "payment_id",
                "valueof_customdata": "99999",
            }
        ]

        response = self._post_webhook(payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_pending_verification_is_ignored_with_200(self, mocked_verify):
        mocked_verify.return_value = PaymentVerificationResult(
            status="pending",
            response_code="00",
        )

        response = self._post_webhook(self._webhook_payload(status="pending"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")


@override_settings(**LIGDICASH_SETTINGS)
class OrderFulfillmentServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="fulfillment@example.com",
            email="fulfillment@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Bags")
        self.product = Product.objects.create(
            name="Backpack",
            category=self.category,
            price="100.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=5)
        self.order = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2)
        self.payment = Payment.objects.create(
            order=self.order,
            amount="200.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="completed",
            order_reference=f"LOBEL-ORDER-{self.order.id}",
            external_transaction_id="LIGDI-REQ-FULFILL",
            currency="XOF",
        )

    def test_payment_service_fulfills_order_and_marks_processed(self):
        PaymentService().handle_payment_completed(self.payment)

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.variant.refresh_from_db()

        self.assertIsNotNone(self.payment.processed_at)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertTrue(self.order.complete)
        self.assertEqual(self.variant.stock, 3)

    def test_payment_service_is_idempotent(self):
        PaymentService().handle_payment_completed(self.payment)
        self.variant.refresh_from_db()
        stock_after_first_call = self.variant.stock

        PaymentService().handle_payment_completed(self.payment)
        self.variant.refresh_from_db()

        self.assertEqual(self.variant.stock, stock_after_first_call)

    def test_order_service_raises_on_insufficient_stock(self):
        self.variant.stock = 1
        self.variant.save(update_fields=["stock"])

        with self.assertRaises(InsufficientStockError):
            OrderService().fulfill_order(self.order, self.payment)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING)
        self.assertFalse(self.order.complete)


@override_settings(**LIGDICASH_SETTINGS)
class PaymentWebhookFulfillmentIntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="retry@example.com",
            email="retry@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Wearables")
        self.product = Product.objects.create(
            name="Watch",
            category=self.category,
            price="150.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=4)
        self.order = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2)
        self.payment = Payment.objects.create(
            order=self.order,
            amount="300.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="pending",
            session_token="ligdi_retry_token",
            order_reference=f"LOBEL-ORDER-{self.order.id}",
            currency="XOF",
        )
        self.url = reverse("payment-webhook")

    def _completed_payload(self, request_id="LIGDI-REQ-RETRY-SAFE"):
        return {
            "response_code": "00",
            "status": "completed",
            "request_id": request_id,
            "custom_data": [
                {
                    "keyof_customdata": "payment_id",
                    "valueof_customdata": str(self.payment.id),
                }
            ],
        }

    def _post_webhook(self, payload):
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return self.client.post(
            self.url,
            data=raw_body,
            content_type="application/json",
        )

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_double_webhook_does_not_double_decrement_stock(self, mocked_verify):
        mocked_verify.return_value = PaymentVerificationResult(
            status="completed",
            response_code="00",
            external_transaction_id="LIGDI-REQ-RETRY-SAFE",
        )

        first_response = self._post_webhook(self._completed_payload())
        second_response = self._post_webhook(self._completed_payload())

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 2)

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_insufficient_stock_webhook_rolls_back_and_returns_500(self, mocked_verify):
        mocked_verify.return_value = PaymentVerificationResult(
            status="completed",
            response_code="00",
            external_transaction_id="LIGDI-REQ-STOCK",
        )
        self.variant.stock = 1
        self.variant.save(update_fields=["stock"])

        response = self._post_webhook(self._completed_payload("LIGDI-REQ-STOCK"))

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")
        self.assertIsNone(self.payment.processed_at)
        self.assertEqual(self.order.status, Order.STATUS_PENDING)
        self.assertFalse(self.order.complete)
        self.assertEqual(self.variant.stock, 1)


@override_settings(**LIGDICASH_SETTINGS)
class WebhookEventDeduplicationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dedup@example.com",
            email="dedup@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Dedup")
        self.product = Product.objects.create(
            name="Belt",
            category=self.category,
            price="50.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=3)
        self.order = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)
        self.payment = Payment.objects.create(
            order=self.order,
            amount="50.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="pending",
            session_token="ligdi_dedup_token",
            order_reference=f"LOBEL-ORDER-{self.order.id}",
            currency="XOF",
        )
        self.url = reverse("payment-webhook")

    def _completed_payload(self):
        return {
            "response_code": "00",
            "status": "completed",
            "request_id": "LIGDI-REQ-DEDUP",
            "custom_data": [
                {
                    "keyof_customdata": "payment_id",
                    "valueof_customdata": str(self.payment.id),
                }
            ],
        }

    def _post_webhook(self, payload):
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return self.client.post(
            self.url,
            data=raw_body,
            content_type="application/json",
        )

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_identical_webhook_payload_is_deduplicated(self, mocked_verify):
        mocked_verify.return_value = PaymentVerificationResult(
            status="completed",
            response_code="00",
            external_transaction_id="LIGDI-REQ-DEDUP",
        )
        payload = self._completed_payload()
        first_response = self._post_webhook(payload)
        second_response = self._post_webhook(payload)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 2)

    @patch("payments.providers.ligdicash.LigdicashProvider.verify_payment")
    def test_logical_deduplication_key_uses_request_id(self, mocked_verify):
        mocked_verify.return_value = PaymentVerificationResult(
            status="completed",
            response_code="00",
            external_transaction_id="LIGDI-REQ-DEDUP",
        )
        self._post_webhook(self._completed_payload())

        event = PaymentWebhookEvent.objects.get()
        self.assertEqual(event.deduplication_key, "ligdicash:request:LIGDI-REQ-DEDUP")


class ConcurrentStockFulfillmentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="stock@example.com",
            email="stock@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user, country="SN")
        self.category = Category.objects.create(name="Limited")
        self.product = Product.objects.create(
            name="Limited Item",
            category=self.category,
            price="80.00",
        )
        self.variant = ProductVariant.objects.create(product=self.product, stock=1)

        self.order_one = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=self.order_one, product=self.product, quantity=1)
        self.payment_one = Payment.objects.create(
            order=self.order_one,
            amount="80.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="completed",
            order_reference=f"LOBEL-ORDER-{self.order_one.id}",
            external_transaction_id="PAY-ONE",
            currency="XOF",
        )

        self.order_two = Order.objects.create(customer=self.customer, complete=False)
        OrderItem.objects.create(order=self.order_two, product=self.product, quantity=1)
        self.payment_two = Payment.objects.create(
            order=self.order_two,
            amount="80.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="completed",
            order_reference=f"LOBEL-ORDER-{self.order_two.id}",
            external_transaction_id="PAY-TWO",
            currency="XOF",
        )

    def test_only_one_order_can_consume_last_stock_unit(self):
        PaymentService().handle_payment_completed(self.payment_one)

        self.variant.refresh_from_db()
        self.order_one.refresh_from_db()
        self.order_two.refresh_from_db()

        self.assertEqual(self.order_one.status, Order.STATUS_PAID)
        self.assertEqual(self.variant.stock, 0)

        with self.assertRaises(InsufficientStockError):
            PaymentService().handle_payment_completed(self.payment_two)

        self.order_two.refresh_from_db()
        self.assertEqual(self.order_two.status, Order.STATUS_PENDING)
        self.assertFalse(self.order_two.complete)


class OrderStatusModelTests(APITestCase):
    def test_order_supports_production_statuses(self):
        expected_statuses = {
            Order.STATUS_PENDING,
            Order.STATUS_PAID,
            Order.STATUS_FAILED,
            Order.STATUS_CANCELLED,
            Order.STATUS_REFUNDED,
        }
        model_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
        self.assertTrue(expected_statuses.issubset(model_statuses))
