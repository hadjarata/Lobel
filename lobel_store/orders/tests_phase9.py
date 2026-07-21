from datetime import timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from pypdf import PdfReader

from orders.models import (
    CommercialDataDeletionError, Order, OrderNotificationReceipt, OrderReceipt,
)
from orders.services.cart_service import CartService
from orders.services.expiration_service import OrderExpirationService
from orders.services.lifecycle_service import (
    ALLOWED_ORDER_TRANSITIONS, OrderLifecycleService, OrderTransitionError,
)
from orders.services.notification_service import OrderNotificationService
from payments.models import Payment
from products.models import Category, Product, ProductVariant
from users.models import Customer


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@lobelstore.test",
    FRONTEND_URL="https://shop.example.test",
    ORDER_PENDING_PAYMENT_TTL_MINUTES=60,
)
class Phase9OrderLifecycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("phase9@example.test")
        self.other = User.objects.create_user("other-phase9@example.test")
        self.customer = Customer.objects.create(user=self.user)
        Customer.objects.create(user=self.other)
        category = Category.objects.create(name="Phase 9")
        product = Product.objects.create(
            name="Snapshot produit", category=category, price=Decimal("1000.00")
        )
        self.variant = ProductVariant.objects.create(
            product=product, stock=10, sku="PHASE9"
        )
        item, _ = CartService().add_variant(
            customer=self.customer, variant=self.variant, quantity=2
        )
        self.order = item.order
        item.product_name = "Nom historique"
        item.variant_name = "Variante historique"
        item.unit_price = Decimal("1000.00")
        item.subtotal = Decimal("2000.00")
        item.currency = "XOF"
        item.save()
        self.order.snapshot_at = timezone.now()
        self.order.customer_email = "phase9@example.test"
        self.order.delivery_recipient_name = "Client Phase"
        self.order.delivery_address = "Adresse historique minimale"
        self.order.subtotal_amount = Decimal("2000.00")
        self.order.shipping_amount = Decimal("500.00")
        self.order.total_amount = Decimal("2500.00")
        self.order.save()
        OrderLifecycleService().transition_order(
            order=self.order,
            target_status=Order.STATUS_PENDING_PAYMENT,
            actor=self.user,
            source="test",
        )
        self.client = APIClient()

    def payment(self, status="completed"):
        return Payment.objects.create(
            order=self.order, amount=self.order.total_amount, currency="XOF",
            payment_method="mock", provider="mock", status=status,
            merchant_reference=f"LOBEL-PHASE9-{Payment.objects.count()}",
        )

    def pay(self, metadata=None):
        payment = self.payment()
        OrderLifecycleService().transition_order(
            order=self.order, target_status=Order.STATUS_PAID,
            payment=payment, source="payment", metadata=metadata,
        )
        self.order.refresh_from_db()
        return payment

    def test_transition_matrix_has_no_paid_to_pending_or_cancelled(self):
        self.assertNotIn(
            Order.STATUS_PENDING_PAYMENT,
            ALLOWED_ORDER_TRANSITIONS[Order.STATUS_PAID],
        )
        self.assertNotIn(
            Order.STATUS_CANCELLED,
            ALLOWED_ORDER_TRANSITIONS[Order.STATUS_PAID],
        )

    def test_repeated_transition_creates_one_history_event(self):
        payment = self.payment(status="pending")
        service = OrderLifecycleService()
        service.transition_order(
            order=self.order, target_status=Order.STATUS_PAYMENT_PROCESSING,
            payment=payment, source="payment",
        )
        _, changed = service.transition_order(
            order=self.order, target_status=Order.STATUS_PAYMENT_PROCESSING,
            payment=payment, source="payment",
        )
        self.assertFalse(changed)
        self.assertEqual(
            self.order.status_history.filter(
                to_status=Order.STATUS_PAYMENT_PROCESSING
            ).count(), 1,
        )

    def test_business_dates_are_written_once(self):
        self.pay()
        paid_at = self.order.paid_at
        _, changed = OrderLifecycleService().transition_order(
            order=self.order, target_status=Order.STATUS_PAID,
            payment=self.order.payments.first(),
        )
        self.order.refresh_from_db()
        self.assertFalse(changed)
        self.assertEqual(self.order.paid_at, paid_at)

    def test_paid_order_cannot_expire_or_cancel(self):
        self.pay()
        for target in (Order.STATUS_EXPIRED, Order.STATUS_CANCELLED):
            with self.assertRaises(OrderTransitionError):
                OrderLifecycleService().transition_order(
                    order=self.order, target_status=target,
                    reason_code="customer_request",
                )

    def test_old_unpaid_order_expires_idempotently(self):
        Order.objects.filter(pk=self.order.pk).update(
            date_ordered=timezone.now() - timedelta(hours=2)
        )
        order, changed = OrderExpirationService().expire(self.order)
        self.assertTrue(changed)
        order, changed = OrderExpirationService().expire(order)
        self.assertFalse(changed)
        self.assertIsNotNone(order.expired_at)

    def test_recent_order_is_not_an_expiration_candidate(self):
        self.assertFalse(
            OrderExpirationService().candidates(order_id=self.order.id).exists()
        )

    def test_completed_payment_excludes_expiration(self):
        self.payment()
        Order.objects.filter(pk=self.order.pk).update(
            date_ordered=timezone.now() - timedelta(hours=2)
        )
        self.assertFalse(
            OrderExpirationService().candidates(order_id=self.order.id).exists()
        )

    def test_expiration_dry_run_does_not_mutate(self):
        Order.objects.filter(pk=self.order.pk).update(
            date_ordered=timezone.now() - timedelta(hours=2)
        )
        output = StringIO()
        call_command(
            "expire_pending_orders", "--dry-run",
            f"--order-id={self.order.id}", stdout=output,
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING_PAYMENT)
        self.assertIn("DRY-RUN", output.getvalue())

    def test_notification_is_sent_once_after_commit(self):
        payment = self.payment(status="pending")
        with self.captureOnCommitCallbacks(execute=True):
            OrderLifecycleService().transition_order(
                order=self.order,
                target_status=Order.STATUS_PAYMENT_PROCESSING,
                payment=payment,
                source="payment",
            )
        receipt = OrderNotificationReceipt.objects.get(
            order=self.order, event_code="payment_processing"
        )
        self.assertEqual(receipt.status, "sent")
        self.assertEqual(len(mail.outbox), 1)
        self.assertFalse(OrderNotificationService.dispatch(receipt.id))
        self.assertEqual(len(mail.outbox), 1)

    def test_notification_failure_does_not_rollback_transition(self):
        payment = self.payment(status="pending")
        with patch(
            "orders.services.notification_service.EmailMultiAlternatives.send",
            side_effect=RuntimeError("SMTP unavailable"),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                OrderLifecycleService().transition_order(
                    order=self.order,
                    target_status=Order.STATUS_PAYMENT_PROCESSING,
                    payment=payment,
                )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PAYMENT_PROCESSING)
        self.assertEqual(
            OrderNotificationReceipt.objects.get(
                order=self.order, event_code="payment_processing"
            ).status,
            OrderNotificationReceipt.STATUS_FAILED,
        )

    def test_notification_receipt_is_append_only(self):
        receipt = OrderNotificationReceipt.objects.create(
            order=self.order, event_code="manual", channel="email",
            recipient_hash="a" * 64,
        )
        with self.assertRaises(CommercialDataDeletionError):
            receipt.delete()

    def test_owner_can_download_snapshot_receipt(self):
        self.pay()
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/orders/orders/{self.order.id}/receipt/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertRegex(
            response["Content-Disposition"],
            r'attachment; filename="lobelstore-justificatif-'
            r'LOBEL-RCPT-\d{4}-\d{6}\.pdf"',
        )
        content = "\n".join(
            page.extract_text() or ""
            for page in PdfReader(BytesIO(response.content)).pages
        )
        self.assertIn("Nom historique", content)
        self.assertIn("2500.00", content)
        self.assertIn("facture fiscale certifiée", content)
        self.assertIn(self.order.receipt.receipt_number, content)

    def test_receipt_is_issued_once_with_immutable_snapshot(self):
        payment = self.pay()
        receipt = OrderReceipt.objects.get(order=self.order)
        original_number = receipt.receipt_number
        original_snapshot = receipt.snapshot

        _, changed = OrderLifecycleService().transition_order(
            order=self.order,
            target_status=Order.STATUS_PAID,
            payment=payment,
            source="replayed_callback",
        )

        self.assertFalse(changed)
        self.assertEqual(OrderReceipt.objects.filter(order=self.order).count(), 1)
        receipt.refresh_from_db()
        self.assertEqual(receipt.receipt_number, original_number)
        self.assertEqual(receipt.snapshot, original_snapshot)

    def test_receipt_snapshot_does_not_read_changed_catalogue(self):
        self.pay()
        receipt = OrderReceipt.objects.get(order=self.order)
        self.variant.product.name = "Nouveau nom catalogue"
        self.variant.product.price = Decimal("999999.00")
        self.variant.product.save()

        self.assertEqual(receipt.snapshot["items"][0]["product"], "Nom historique")
        self.assertEqual(receipt.snapshot["items"][0]["unit_price"], "1000.00")
        self.assertEqual(
            receipt.snapshot["customer"]["address"],
            "Adresse historique minimale",
        )

    def test_receipt_render_error_does_not_change_paid_order(self):
        self.pay()
        self.client.force_authenticate(self.user)
        with patch(
            "orders.views.render_order_receipt_pdf",
            side_effect=RuntimeError("renderer failure"),
        ):
            response = self.client.get(
                f"/api/orders/orders/{self.order.id}/receipt/"
            )
        self.assertEqual(response.status_code, 500)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertIsNotNone(self.order.paid_at)
        self.assertEqual(OrderReceipt.objects.filter(order=self.order).count(), 1)

    def test_other_user_cannot_read_order_or_receipt(self):
        self.pay()
        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.get(f"/api/orders/orders/{self.order.id}/").status_code, 404
        )
        self.assertEqual(
            self.client.get(
                f"/api/orders/orders/{self.order.id}/receipt/"
            ).status_code, 404,
        )

    def test_public_timeline_hides_internal_metadata_and_actor(self):
        self.pay(metadata={"secret": "hidden"})
        self.client.force_authenticate(self.user)
        data = self.client.get(f"/api/orders/orders/{self.order.id}/").json()
        rendered = str(data["timeline"])
        self.assertNotIn("secret", rendered)
        self.assertNotIn("actor", rendered)

    def test_list_contract_exposes_server_actions(self):
        self.client.force_authenticate(self.user)
        result = self.client.get("/api/orders/orders/").json()["results"][0]
        self.assertTrue(result["can_pay"])
        self.assertTrue(result["can_cancel"])
        self.assertEqual(result["total_amount"], "2500.00")

    def test_cancel_endpoint_requires_owner_and_reason(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(
            self.client.post(
                f"/api/orders/orders/{self.order.id}/cancel/", {}, format="json"
            ).status_code,
            400,
        )
        response = self.client.post(
            f"/api/orders/orders/{self.order.id}/cancel/",
            {"reason": "Je souhaite annuler"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Order.STATUS_CANCELLED)

    def test_receipt_unavailable_before_payment(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/orders/orders/{self.order.id}/receipt/")
        self.assertEqual(response.status_code, 409)
