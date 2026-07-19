from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from users.models import Customer


class OrderWriteProtectionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(user=self.user)
        self.other_customer = Customer.objects.create(user=self.other_user)
        self.order = Order.objects.create(customer=self.customer)
        self.other_order = Order.objects.create(customer=self.other_customer)
        self.client.force_authenticate(self.user)

    def test_client_lists_and_retrieves_only_own_orders(self):
        response = self.client.get("/api/orders/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([entry["id"] for entry in response.data], [self.order.id])

        own_response = self.client.get(f"/api/orders/orders/{self.order.id}/")
        self.assertEqual(own_response.status_code, status.HTTP_200_OK)

        other_response = self.client.get(
            f"/api/orders/orders/{self.other_order.id}/"
        )
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_cannot_create_order_directly(self):
        response = self.client.post("/api/orders/orders/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_client_cannot_put_patch_or_delete_order(self):
        url = f"/api/orders/orders/{self.order.id}/"

        put_response = self.client.put(
            url,
            {"status": "paid", "complete": True},
            format="json",
        )
        patch_response = self.client.patch(
            url,
            {
                "status": "paid",
                "complete": True,
                "transaction_id": "CLIENT-CONTROLLED",
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

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING)
        self.assertFalse(self.order.complete)
        self.assertIsNone(self.order.transaction_id)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())
