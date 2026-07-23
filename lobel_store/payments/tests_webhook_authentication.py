import json
from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from payments.checks import payment_configuration_check
from payments.models import PaymentWebhookEvent
from payments.providers.base import WebhookAuthenticityResult
from payments.providers.mock import MockProvider
from payments.services.webhook_security import (
    WebhookAuthenticationError,
    WebhookSecurityService,
)
from payments.services.webhook_service import PaymentWebhookService


class SignedMockProvider(MockProvider):
    def __init__(
        self, *, verified=True, implemented=True,
        event_id="evt_immutable_1", occurred_at=None,
    ):
        self.auth_result = WebhookAuthenticityResult(
            verified=verified,
            verification_implemented=implemented,
            method="hmac-sha256",
            event_id=event_id,
            occurred_at=occurred_at or timezone.now(),
        )

    def verify_webhook_authenticity(self, raw_body, headers, payload):
        return self.auth_result


@override_settings(
    PAYMENT_WEBHOOK_SIGNATURE_REQUIRED=True,
    PAYMENT_WEBHOOK_ALLOWED_IPS=["203.0.113.0/24"],
    PAYMENT_WEBHOOK_MAX_AGE_SECONDS=300,
)
class WebhookSecurityPolicyTests(SimpleTestCase):
    def authenticate(self, provider=None, source_ip="203.0.113.10"):
        return WebhookSecurityService().authenticate(
            provider=provider or SignedMockProvider(),
            raw_body=b'{"event":"payment"}',
            headers={"X-Signature": "opaque"},
            payload={"event": "payment"},
            source_ip=source_ip,
        )

    def test_valid_signature_timestamp_event_and_ip_are_accepted(self):
        result = self.authenticate()
        self.assertTrue(result.signature_verified)
        self.assertEqual(result.authentication_method, "hmac-sha256")
        self.assertEqual(result.provider_event_id, "evt_immutable_1")
        self.assertEqual(len(result.source_ip_hash), 64)

    def test_invalid_or_unimplemented_signature_is_rejected(self):
        for provider in (
            SignedMockProvider(verified=False),
            SignedMockProvider(implemented=False),
        ):
            with self.subTest(provider=provider.auth_result):
                with self.assertRaises(WebhookAuthenticationError):
                    self.authenticate(provider)

    def test_missing_event_id_is_rejected(self):
        with self.assertRaises(WebhookAuthenticationError):
            self.authenticate(SignedMockProvider(event_id=None))

    def test_stale_and_future_timestamps_are_rejected(self):
        for occurred_at in (
            timezone.now() - timedelta(minutes=10),
            timezone.now() + timedelta(minutes=10),
        ):
            with self.subTest(occurred_at=occurred_at):
                with self.assertRaises(WebhookAuthenticationError):
                    self.authenticate(
                        SignedMockProvider(occurred_at=occurred_at)
                    )

    def test_source_outside_allowlist_is_rejected(self):
        with self.assertRaises(WebhookAuthenticationError):
            self.authenticate(source_ip="198.51.100.5")


@override_settings(
    PAYMENT_WEBHOOK_SIGNATURE_REQUIRED=True,
    PAYMENT_WEBHOOK_ALLOWED_IPS=["203.0.113.10"],
    PAYMENT_WEBHOOK_MAX_AGE_SECONDS=300,
)
class AuthenticatedWebhookReplayTests(TestCase):
    def test_signed_immutable_event_id_is_deduplicated_and_traced(self):
        provider = SignedMockProvider(event_id="evt_same")
        service = PaymentWebhookService(payment_provider=provider)
        first_body = json.dumps(
            {"payment_id": 999999, "status": "completed", "nonce": 1}
        ).encode()
        replay_body = json.dumps(
            {"payment_id": 999999, "status": "completed", "nonce": 2}
        ).encode()

        first = service.process(
            first_body,
            "application/json",
            headers={"X-Signature": "first"},
            source_ip="203.0.113.10",
        )
        replay = service.process(
            replay_body,
            "application/json",
            headers={"X-Signature": "second"},
            source_ip="203.0.113.10",
        )

        self.assertEqual(first.message, "Unknown payment.")
        self.assertEqual(replay.message, "Duplicate event.")
        event = PaymentWebhookEvent.objects.get()
        self.assertTrue(event.signature_verified)
        self.assertEqual(event.authentication_method, "hmac-sha256")
        self.assertEqual(event.provider_event_id, "evt_same")
        self.assertEqual(
            event.deduplication_key, "mock:event:evt_same"
        )
        self.assertEqual(len(event.source_ip_hash), 64)


class WebhookSecurityConfigurationTests(SimpleTestCase):
    @override_settings(
        DEBUG=False,
        PAYMENT_PROVIDER="ligdicash",
        LIGDICASH_API_KEY="key",
        LIGDICASH_API_TOKEN="token",
        LIGDICASH_BASE_URL="https://app.ligdicash.com",
        LIGDICASH_RETURN_URL="https://shop.example.com/return",
        LIGDICASH_CANCEL_URL="https://shop.example.com/cancel",
        LIGDICASH_CALLBACK_URL="https://api.example.com/webhook",
        LIGDICASH_HTTP_TIMEOUT=15,
        LIGDICASH_VERIFY_TLS=True,
        PAYMENT_WEBHOOK_SIGNATURE_REQUIRED=True,
    )
    def test_cannot_enable_unimplemented_ligdicash_signature(self):
        self.assertEqual(payment_configuration_check(None)[0].id, "payments.E008")

    @override_settings(
        DEBUG=True,
        PAYMENT_PROVIDER="mock",
        PAYMENT_WEBHOOK_ALLOWED_IPS=["not-an-ip"],
    )
    def test_invalid_allowlist_fails_system_check(self):
        self.assertEqual(payment_configuration_check(None)[0].id, "payments.E009")


class WebhookAuthenticationResponseTests(TestCase):
    @patch(
        "payments.views.PaymentWebhookService.process",
        side_effect=WebhookAuthenticationError("invalid"),
    )
    def test_authentication_failure_returns_401(self, _process):
        response = APIClient().post(
            reverse("payment-webhook"),
            data=b'{"status":"completed"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 0)
