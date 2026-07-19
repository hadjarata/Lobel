from django.contrib.auth.models import User
from django.test import TestCase

from .serializers import RegisterSerializer


class PasswordValidationTests(TestCase):
    def payload(self, password):
        return {
            "email": "client@example.com", "password": password,
            "country": "ML", "phone_number": "",
        }

    def test_weak_passwords_are_rejected(self):
        for password in ("short", "password", "123456789012"):
            serializer = RegisterSerializer(data=self.payload(password))
            self.assertFalse(serializer.is_valid(), password)
            self.assertIn("password", serializer.errors)

    def test_valid_password_is_hashed(self):
        serializer = RegisterSerializer(data=self.payload("N0tes!River-Cloud-92"))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        customer = serializer.save()
        self.assertNotEqual(customer.user.password, "N0tes!River-Cloud-92")
        self.assertTrue(customer.user.check_password("N0tes!River-Cloud-92"))

    def test_password_similar_to_email_is_rejected(self):
        serializer = RegisterSerializer(data=self.payload("client@example.com2026"))
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
