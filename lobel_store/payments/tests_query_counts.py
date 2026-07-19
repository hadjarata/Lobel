from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from orders.models import Order
from users.models import Customer
from .models import Payment


class PaymentQueryCountTests(TestCase):
    def setUp(self):
        user = User.objects.create_user("query-payments")
        self.customer = Customer.objects.create(user=user)
        self.client = APIClient()
        self.client.force_authenticate(user)

    def create_payment(self):
        order = Order.objects.create(customer=self.customer, complete=True, status=Order.STATUS_PAID)
        return Payment.objects.create(order=order, amount=1, payment_method="cash")

    def count(self):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get("/api/payments/payments/")
            self.assertEqual(response.status_code, 200, response.data)
        return len(captured)

    def test_payment_list_query_count_is_stable(self):
        self.create_payment()
        one = self.count()
        for _ in range(9):
            self.create_payment()
        ten = self.count()
        self.assertLessEqual(ten, one)
        self.assertLessEqual(ten, 2)
