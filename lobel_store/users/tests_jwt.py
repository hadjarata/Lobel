from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Customer
from .services import suspend_user


class JWTTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "jwt@example.com", "jwt@example.com", "Strong!Password-2026"
        )
        Customer.objects.create(user=self.user, email_verified_at=timezone.now())
        self.client = APIClient()

    def login(self):
        return self.client.post(
            "/api/token/",
            {"username": "JWT@EXAMPLE.COM", "password": "Strong!Password-2026"},
            format="json",
        )

    def test_login_rotation_and_old_refresh_blacklist(self):
        login = self.login()
        self.assertEqual(login.status_code, 200, login.data)
        first = login.data["refresh"]
        rotated = self.client.post("/api/token/refresh/", {"refresh": first}, format="json")
        self.assertEqual(rotated.status_code, 200, rotated.data)
        self.assertIn("refresh", rotated.data)
        reused = self.client.post("/api/token/refresh/", {"refresh": first}, format="json")
        self.assertEqual(reused.status_code, 401)

    def test_logout_is_idempotent_and_refresh_is_revoked(self):
        refresh = self.login().data["refresh"]
        self.assertEqual(
            self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code,
            204,
        )
        self.assertEqual(
            self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code,
            204,
        )
        self.assertEqual(
            self.client.post("/api/token/refresh/", {"refresh": refresh}, format="json").status_code,
            401,
        )

    def test_suspension_blocks_login_and_existing_refresh(self):
        refresh = self.login().data["refresh"]
        suspend_user(self.user, reason="test")
        self.assertEqual(
            self.client.post("/api/token/refresh/", {"refresh": refresh}, format="json").status_code,
            401,
        )
        self.assertEqual(self.login().status_code, 401)
