import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from payments.checks import payment_configuration_check
from payments.models import Payment
from payments.providers import get_payment_provider
from payments.providers.base import (
    PaymentConfigurationError,
    PaymentInvalidResponseError,
    PaymentVerificationResult,
    validate_provider_confirmation,
)
from payments.providers.mock import MockProvider
from users.models import Customer


class PaymentProviderConfigurationTests(SimpleTestCase):
    @override_settings(DEBUG=True, PAYMENT_PROVIDER="mock")
    def test_explicit_mock_is_allowed_in_debug(self):
        self.assertIsInstance(get_payment_provider(), MockProvider)
        self.assertEqual(payment_configuration_check(None), [])

    @override_settings(DEBUG=True, PAYMENT_PROVIDER="")
    def test_missing_provider_is_rejected_in_debug(self):
        with self.assertRaises(PaymentConfigurationError):
            get_payment_provider()
        self.assertEqual(payment_configuration_check(None)[0].id, "payments.E001")

    @override_settings(DEBUG=False, TESTING=False, PAYMENT_PROVIDER="")
    def test_missing_provider_is_rejected_in_production(self):
        with self.assertRaises(PaymentConfigurationError):
            get_payment_provider()

    @override_settings(DEBUG=False, TESTING=False, PAYMENT_PROVIDER="mock")
    def test_mock_is_rejected_in_production(self):
        with self.assertRaises(PaymentConfigurationError):
            get_payment_provider()
        self.assertEqual(payment_configuration_check(None)[0].id, "payments.E003")

    @override_settings(
        DEBUG=False,
        TESTING=False,
        PAYMENT_PROVIDER="unknown-provider",
    )
    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(PaymentConfigurationError):
            get_payment_provider()
        self.assertEqual(payment_configuration_check(None)[0].id, "payments.E002")

    @override_settings(DEBUG=False, TESTING=False, PAYMENT_PROVIDER="ligdicash")
    def test_real_provider_is_accepted_but_confirmations_remain_fail_closed(self):
        self.assertEqual(payment_configuration_check(None)[0].id, "payments.E004")


class ProviderConfirmationValidationTests(SimpleTestCase):
    def setUp(self):
        self.payment = Payment(
            amount=Decimal("1000.00"),
            currency="XOF",
            order_reference="LOBEL-ORDER-42",
        )

    def result(self, **overrides):
        values = {
            "status": "completed",
            "response_code": "00",
            "provider": "mock",
            "provider_reference": "LOBEL-ORDER-42",
            "verified_amount": Decimal("1000.00"),
            "verified_currency": "XOF",
            "signature_verified": True,
            "verification_implemented": True,
        }
        values.update(overrides)
        return PaymentVerificationResult(**values)

    def validate(self, result=None, *, require_signature=True):
        validate_provider_confirmation(
            payment=self.payment,
            result=result or self.result(),
            require_signature=require_signature,
        )

    def test_matching_confirmation_is_accepted(self):
        self.validate()

    def test_lower_and_higher_amounts_are_rejected(self):
        for amount in (Decimal("999.00"), Decimal("1001.00")):
            with self.subTest(amount=amount):
                with self.assertRaises(PaymentInvalidResponseError):
                    self.validate(self.result(verified_amount=amount))

    def test_missing_amount_is_rejected(self):
        with self.assertRaises(PaymentInvalidResponseError):
            self.validate(self.result(verified_amount=None))

    def test_missing_or_different_currency_is_rejected(self):
        for currency in (None, "EUR"):
            with self.subTest(currency=currency):
                with self.assertRaises(PaymentInvalidResponseError):
                    self.validate(self.result(verified_currency=currency))

    def test_non_success_status_is_rejected(self):
        with self.assertRaises(PaymentInvalidResponseError):
            self.validate(self.result(status="pending"))

    def test_missing_or_mismatched_reference_is_rejected(self):
        for reference in (None, "LOBEL-ORDER-OTHER"):
            with self.subTest(reference=reference):
                with self.assertRaises(PaymentInvalidResponseError):
                    self.validate(self.result(provider_reference=reference))

    def test_unverified_signature_is_rejected_when_required(self):
        with self.assertRaises(PaymentInvalidResponseError):
            self.validate(self.result(signature_verified=False))

    def test_unimplemented_verification_is_rejected(self):
        with self.assertRaises(PaymentInvalidResponseError):
            self.validate(self.result(verification_implemented=False))


class ProductionPaymentEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="production-payer@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.order = Order.objects.create(customer=self.customer)
        self.payment = Payment.objects.create(
            order=self.order,
            amount="1000.00",
            payment_method="mock",
            provider="mock",
            status="pending",
            session_token="mock-production-token",
            order_reference=f"LOBEL-ORDER-{self.order.id}",
            currency="XOF",
        )
        self.client.force_authenticate(self.user)

    @override_settings(DEBUG=False, TESTING=False, PAYMENT_PROVIDER="mock")
    def test_mock_confirmation_is_hidden_in_production(self):
        response = self.client.post(
            reverse("payment-mock-confirm"),
            {"paymentId": self.payment.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")
        self.assertIsNone(self.payment.processed_at)
        self.assertEqual(self.order.status, Order.STATUS_PENDING)
        self.assertFalse(self.order.complete)

    @override_settings(DEBUG=False, TESTING=False, PAYMENT_PROVIDER="ligdicash")
    def test_unverified_production_webhook_is_refused(self):
        payload = {
            "status": "completed",
            "custom_data": {
                "payment_id": str(self.payment.id),
            },
        }
        response = self.client.post(
            reverse("payment-webhook"),
            data=json.dumps(payload).encode("utf-8"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")
        self.assertEqual(self.order.status, Order.STATUS_PENDING)
