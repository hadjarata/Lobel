import json
from unittest.mock import patch

from django.test import TestCase, override_settings

from payments.providers.base import PaymentVerificationResult
from payments.providers.ligdicash import LigdicashProvider


LIGDICASH_SETTINGS = {
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
class LigdicashProviderTests(TestCase):
    def setUp(self):
        self.provider = LigdicashProvider()

    def test_extract_payment_id_from_custom_data_array(self):
        payload = {
            "custom_data": [
                {
                    "keyof_customdata": "payment_id",
                    "valueof_customdata": "42",
                }
            ]
        }
        self.assertEqual(self.provider.extract_payment_id(payload), 42)

    def test_extract_payment_id_from_transaction_id_prefix(self):
        payload = {
            "custom_data": [
                {
                    "keyof_customdata": "transaction_id",
                    "valueof_customdata": "LOBEL-PAYMENT-17",
                }
            ]
        }
        self.assertEqual(self.provider.extract_payment_id(payload), 17)

    def test_build_deduplication_key_uses_request_id(self):
        payload = {"request_id": "P2771491712026", "status": "completed"}
        key = self.provider.build_deduplication_key(payload, "abc123")
        self.assertEqual(key, "ligdicash:request:P2771491712026")

    def test_parse_webhook_supports_json_and_form_encoded(self):
        json_payload = {
            "status": "completed",
            "custom_data": [{"keyof_customdata": "payment_id", "valueof_customdata": "1"}],
        }
        raw_json = json.dumps(json_payload).encode("utf-8")
        parsed_json = self.provider.parse_webhook(raw_json, "application/json")
        self.assertEqual(parsed_json["status"], "completed")

        raw_form = b"status=completed&request_id=P123"
        parsed_form = self.provider.parse_webhook(raw_form, "application/x-www-form-urlencoded")
        self.assertEqual(parsed_form["status"], "completed")
        self.assertEqual(parsed_form["request_id"], "P123")

    @patch("payments.providers.ligdicash.LigdicashProvider._get_json")
    def test_verify_payment_returns_verification_result(self, mocked_get):
        mocked_get.return_value = {
            "response_code": "00",
            "status": "completed",
            "request_id": "P2771491712026",
        }

        result = self.provider.verify_payment("stored-token")

        self.assertIsInstance(result, PaymentVerificationResult)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.external_transaction_id, "P2771491712026")
