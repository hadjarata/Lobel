from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient


class ThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def tearDown(self):
        cache.clear()

    def test_login_endpoint_returns_429(self):
        payload = {"username": "nobody@example.com", "password": "invalid"}
        responses = [self.client.post("/api/token/", payload, format="json") for _ in range(11)]
        self.assertEqual(responses[-1].status_code, 429)

    def test_reset_endpoint_returns_429_without_enumeration(self):
        payload = {"email": "nobody@example.com"}
        responses = [
            self.client.post(
                "/api/users/customers/request-password-reset/", payload, format="json"
            )
            for _ in range(6)
        ]
        first, second = responses[0], responses[-1]
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
