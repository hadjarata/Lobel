from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.core import mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from .models import Customer
from .services import suspend_user, unsuspend_user


class AccountLifecycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "client@example.com", "client@example.com", "Old!Password-2026"
        )
        self.customer = Customer.objects.create(
            user=self.user, email_verified_at=timezone.now()
        )
        self.client = APIClient()

    def reset_payload(self, password="New!Password-2026"):
        return {
            "uid": urlsafe_base64_encode(force_bytes(self.user.pk)),
            "token": default_token_generator.make_token(self.user),
            "password": password, "confirm_password": password,
        }

    def test_reset_never_unsuspends_account(self):
        suspend_user(self.user, reason="fraude")
        response = self.client.post(
            "/api/users/customers/reset-password/", self.reset_payload(), format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.customer.refresh_from_db()
        self.assertIsNotNone(self.customer.suspended_at)
        self.assertEqual(self.customer.suspension_reason, "fraude")

    def test_email_activation_never_unsuspends_account(self):
        self.customer.email_verified_at = None
        self.customer.save(update_fields=["email_verified_at"])
        suspend_user(self.user, reason="administration")
        payload = {
            "uid": urlsafe_base64_encode(force_bytes(self.user.pk)),
            "token": default_token_generator.make_token(self.user),
        }
        response = self.client.post(
            "/api/users/customers/verify-email/", payload, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertIsNotNone(self.customer.email_verified_at)
        self.assertTrue(self.customer.is_suspended)

    def test_only_explicit_admin_service_unsuspends(self):
        suspend_user(self.user, reason="test")
        unsuspend_user(self.user)
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_suspended)

    def test_reset_request_does_not_enumerate_accounts_or_return_tokens(self):
        cases = ["client@example.com", "unknown@example.com"]
        suspend_user(self.user, reason="test")
        cases.append("CLIENT@EXAMPLE.COM")
        responses = [
            self.client.post(
                "/api/users/customers/request-password-reset/",
                {"email": email}, format="json",
            )
            for email in cases
        ]
        self.assertTrue(all(response.status_code == 200 for response in responses))
        self.assertTrue(all(response.data == responses[0].data for response in responses))
        self.assertNotIn("token", responses[0].data)
        self.assertNotIn("uid", responses[0].data)
        self.assertEqual(len(mail.outbox), 0)
