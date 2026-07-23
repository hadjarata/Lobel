from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import User
from django.core import mail
from django.db import close_old_connections
from django.db.models import Sum
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order
from payments.models import (
    Payment, PaymentOperationalAlert, Refund, RefundAttempt,
)
from payments.providers.base import PaymentProvider, RefundResult
from payments.services.refund_service import RefundError, RefundService
from payments.services.refund_notification_service import RefundNotificationService
from users.models import Customer


class RefundProvider(PaymentProvider):
    provider_name = "mock"

    def __init__(self, create_status="completed", verify_status="completed"):
        self.create_status = create_status
        self.verify_status = verify_status

    def create_checkout(self, context):
        raise NotImplementedError

    def verify_payment(self, session_token, *, payment=None):
        raise NotImplementedError

    def parse_webhook(self, raw_body, content_type):
        raise NotImplementedError

    def extract_payment_id(self, payload):
        raise NotImplementedError

    def build_deduplication_key(self, payload, payload_hash):
        raise NotImplementedError

    @staticmethod
    def result(refund, status):
        return RefundResult(
            status=status,
            response_code="00" if status != "failed" else "REFUSED",
            provider_reference=f"REF-{refund.uuid}",
            refunded_amount=refund.amount,
            currency=refund.currency,
        )

    def create_refund(self, refund):
        return self.result(refund, self.create_status)

    def verify_refund(self, refund):
        return self.result(refund, self.verify_status)


class RefundFixture:
    def make_payment(self, *, amount="1000.00", payment_status="completed",
                     failure_code="", order_status=Order.STATUS_PAID):
        email = f"refund-{User.objects.count()}@example.com"
        user = User.objects.create_user(
            email,
            email=email,
            is_staff=True,
        )
        customer = Customer.objects.create(user=user)
        order = Order.objects.create(
            customer=customer,
            status=order_status,
            snapshot_at=timezone.now(),
            customer_email=user.email,
            total_amount=Decimal(amount),
            subtotal_amount=Decimal(amount),
            currency="XOF",
            paid_at=timezone.now(),
            stock_consumed_at=timezone.now(),
        )
        payment = Payment.objects.create(
            order=order,
            amount=Decimal(amount),
            currency="XOF",
            payment_method="mock",
            provider="mock",
            status=payment_status,
            provider_status="completed",
            processed_at=timezone.now(),
            failure_code=failure_code,
        )
        return user, order, payment


class RefundWorkflowTests(RefundFixture, TestCase):
    def setUp(self):
        self.provider = RefundProvider()
        self.service = RefundService(provider=self.provider)

    def request(self, payment, amount, key, actor):
        return self.service.request(
            payment=payment,
            amount=Decimal(amount),
            reason="Demande client",
            actor=actor,
            idempotency_key=key,
        )[0]

    def test_partial_then_remaining_full_refund(self):
        actor, order, payment = self.make_payment()
        partial = self.request(payment, "300.00", "partial-1", actor)
        self.assertFalse(partial.affects_order_status)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)

        partial = self.service.process(refund_id=partial.id)
        self.assertEqual(partial.status, Refund.STATUS_COMPLETED)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(
            RefundService.refundable_balance(payment), Decimal("700.00")
        )

        remainder = self.request(payment, "700.00", "partial-2", actor)
        self.assertTrue(remainder.affects_order_status)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_REFUND_PENDING)

        remainder = self.service.process(refund_id=remainder.id)
        order.refresh_from_db()
        self.assertEqual(remainder.status, Refund.STATUS_COMPLETED)
        self.assertEqual(order.status, Order.STATUS_REFUNDED)
        self.assertEqual(
            RefundService.refundable_balance(payment), Decimal("0.00")
        )

    def test_cannot_refund_more_than_available(self):
        actor, _, payment = self.make_payment()
        self.request(payment, "600.00", "limit-1", actor)
        with self.assertRaises(RefundError) as raised:
            self.request(payment, "500.00", "limit-2", actor)
        self.assertEqual(raised.exception.code, "refund_exceeds_available")

    def test_request_is_idempotent_and_conflict_is_rejected(self):
        actor, _, payment = self.make_payment()
        first, replayed = self.service.request(
            payment=payment, amount="250.00", reason="Même demande",
            actor=actor, idempotency_key="same-refund",
        )
        second, second_replayed = self.service.request(
            payment=payment, amount="250.00", reason="Même demande",
            actor=actor, idempotency_key="same-refund",
        )
        self.assertFalse(replayed)
        self.assertTrue(second_replayed)
        self.assertEqual(first.id, second.id)
        with self.assertRaises(RefundError) as raised:
            self.service.request(
                payment=payment, amount="200.00", reason="Autre demande",
                actor=actor, idempotency_key="same-refund",
            )
        self.assertEqual(raised.exception.code, "idempotency_conflict")

    def test_failed_refund_is_journaled_and_can_be_retried(self):
        actor, order, payment = self.make_payment()
        refund = self.request(payment, "1000.00", "retry", actor)
        failed = RefundService(
            provider=RefundProvider(create_status="failed")
        ).process(refund_id=refund.id)
        order.refresh_from_db()
        self.assertEqual(failed.status, Refund.STATUS_FAILED)
        self.assertEqual(order.status, Order.STATUS_REFUND_FAILED)

        completed = self.service.process(refund_id=refund.id)
        order.refresh_from_db()
        self.assertEqual(completed.status, Refund.STATUS_COMPLETED)
        self.assertEqual(order.status, Order.STATUS_REFUNDED)
        self.assertEqual(
            list(refund.attempts.order_by("sequence").values_list(
                "result", flat=True
            )),
            ["failed", "succeeded"],
        )

    def test_processing_refund_is_completed_by_reconciliation(self):
        actor, _, payment = self.make_payment()
        refund = self.request(payment, "1000.00", "reconcile", actor)
        processing = RefundService(
            provider=RefundProvider(create_status="processing")
        ).process(refund_id=refund.id)
        self.assertEqual(processing.status, Refund.STATUS_PROCESSING)

        completed = self.service.reconcile(refund_id=refund.id)
        self.assertEqual(completed.status, Refund.STATUS_COMPLETED)
        self.assertEqual(
            list(refund.attempts.order_by("sequence").values_list(
                "action", flat=True
            )),
            ["submit", "reconcile"],
        )

    def test_failed_refund_cannot_be_retried_after_balance_is_reallocated(self):
        actor, _, payment = self.make_payment()
        failed = self.request(payment, "700.00", "old-failed", actor)
        RefundService(
            provider=RefundProvider(create_status="failed")
        ).process(refund_id=failed.id)
        replacement = self.request(payment, "700.00", "replacement", actor)

        with self.assertRaises(RefundError) as raised:
            self.service.process(refund_id=failed.id)

        self.assertEqual(raised.exception.code, "refund_exceeds_available")
        replacement.refresh_from_db()
        self.assertEqual(replacement.status, Refund.STATUS_REQUESTED)

    def test_duplicate_payment_refund_does_not_change_paid_order(self):
        actor, order, payment = self.make_payment(
            payment_status="refund_required",
            failure_code="duplicate_payment",
        )
        alert = PaymentOperationalAlert.objects.create(
            payment=payment,
            order=order,
            alert_type="duplicate_payment",
            message="Double encaissement",
        )
        refund = self.request(payment, "1000.00", "duplicate", actor)
        self.assertFalse(refund.affects_order_status)
        self.service.process(refund_id=refund.id)

        order.refresh_from_db()
        alert.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(alert.status, "resolved")
        self.assertIsNotNone(alert.resolved_at)

    def test_attempt_history_is_append_only(self):
        actor, _, payment = self.make_payment()
        refund = self.request(payment, "100.00", "append-only", actor)
        self.service.process(refund_id=refund.id)
        attempt = RefundAttempt.objects.get(refund=refund)
        attempt.result = "failed"
        with self.assertRaises(Exception):
            attempt.save()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_customer_is_notified_for_each_refund_stage(self):
        actor, _, payment = self.make_payment()
        refund = self.request(payment, "1000.00", "notifications", actor)
        self.service.process(refund_id=refund.id)
        receipts = list(refund.notification_receipts.order_by("id"))
        for receipt in receipts:
            RefundNotificationService.dispatch(receipt.id)

        self.assertEqual(len(receipts), 3)
        self.assertEqual(len(mail.outbox), 3)
        self.assertTrue(all(str(refund.uuid) in message.body for message in mail.outbox))

    def test_customer_refund_endpoint_creates_idempotent_refund(self):
        actor, order, _ = self.make_payment()
        client = APIClient()
        client.force_authenticate(actor)
        url = f"/api/orders/orders/{order.id}/request-refund/"

        missing_key = client.post(url, {"reason": "Retour"}, format="json")
        first = client.post(
            url,
            {"reason": "Retour"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="customer-refund",
        )
        replay = client.post(
            url,
            {"reason": "Retour"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="customer-refund",
        )

        self.assertEqual(missing_key.status_code, 400)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.data["replayed"])
        self.assertEqual(first.data["refund_id"], replay.data["refund_id"])

    def test_admin_can_create_partial_refund_request(self):
        actor, _, payment = self.make_payment()
        actor.is_superuser = True
        actor.save(update_fields=["is_superuser"])
        client = APIClient()
        client.force_login(actor)

        response = client.post(
            reverse("admin:payments_refund_add"),
            {
                "payment": payment.id,
                "amount": "250.00",
                "reason": "Geste commercial",
                "idempotency_key": "admin-partial-refund",
                "_save": "Enregistrer",
            },
        )

        self.assertEqual(response.status_code, 302)
        refund = Refund.objects.get(
            payment=payment, idempotency_key="admin-partial-refund"
        )
        self.assertEqual(refund.amount, Decimal("250.00"))
        self.assertEqual(refund.status, Refund.STATUS_REQUESTED)
        self.assertEqual(refund.requested_by, actor)


class ConcurrentRefundRequestTests(RefundFixture, TransactionTestCase):
    reset_sequences = True

    @staticmethod
    def _request(payment_id, actor_id, amount, key, barrier):
        close_old_connections()
        barrier.wait()
        try:
            return RefundService(provider=RefundProvider()).request(
                payment=Payment.objects.get(pk=payment_id),
                amount=amount,
                reason="Concurrence",
                actor=User.objects.get(pk=actor_id),
                idempotency_key=key,
            )[0].id
        except RefundError as exc:
            return exc.code
        finally:
            close_old_connections()

    def test_concurrent_requests_cannot_exceed_payment(self):
        actor, _, payment = self.make_payment()
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                future.result()
                for future in (
                    pool.submit(
                        self._request, payment.id, actor.id,
                        Decimal("700.00"), "race-a", barrier,
                    ),
                    pool.submit(
                        self._request, payment.id, actor.id,
                        Decimal("700.00"), "race-b", barrier,
                    ),
                )
            ]
        self.assertEqual(
            sum(isinstance(result, int) for result in results), 1
        )
        self.assertIn("refund_exceeds_available", results)
        self.assertEqual(
            Refund.objects.filter(payment=payment).aggregate(
                total=Sum("amount")
            )["total"],
            Decimal("700.00"),
        )
