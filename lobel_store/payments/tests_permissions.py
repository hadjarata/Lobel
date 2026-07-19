from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from payments.models import Payment
from users.models import Customer


class PaymentWriteProtectionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="payer@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="other-payer@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.other_customer = Customer.objects.create(user=self.other_user)
        self.order = Order.objects.create(customer=self.customer)
        self.other_order = Order.objects.create(customer=self.other_customer)
        self.payment = Payment.objects.create(
            order=self.order,
            amount="10000.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="pending",
            currency="XOF",
        )
        self.other_payment = Payment.objects.create(
            order=self.other_order,
            amount="5000.00",
            payment_method="ligdicash",
            provider="ligdicash",
            status="pending",
            currency="XOF",
        )
        self.client.force_authenticate(self.user)

    def test_client_lists_and_retrieves_only_own_payments(self):
        response = self.client.get("/api/payments/payments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [entry["id"] for entry in response.data],
            [self.payment.id],
        )

        own_response = self.client.get(
            f"/api/payments/payments/{self.payment.id}/"
        )
        self.assertEqual(own_response.status_code, status.HTTP_200_OK)

        other_response = self.client.get(
            f"/api/payments/payments/{self.other_payment.id}/"
        )
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_cannot_create_payment_directly(self):
        response = self.client.post(
            "/api/payments/payments/",
            {
                "order": self.order.id,
                "amount": "1.00",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_client_cannot_put_patch_or_delete_payment(self):
        url = f"/api/payments/payments/{self.payment.id}/"

        put_response = self.client.put(
            url,
            {"amount": "1.00", "status": "completed"},
            format="json",
        )
        patch_response = self.client.patch(
            url,
            {
                "amount": "1.00",
                "status": "completed",
                "external_transaction_id": "CLIENT-CONTROLLED",
                "provider": "mock",
            },
            format="json",
        )
        delete_response = self.client.delete(url)

        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            patch_response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.amount, 10000)
        self.assertEqual(self.payment.status, "pending")
        self.assertIsNone(self.payment.external_transaction_id)
        self.assertEqual(self.payment.provider, "ligdicash")
        self.assertTrue(Payment.objects.filter(pk=self.payment.pk).exists())
