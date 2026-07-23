import hashlib
import json
import logging
from decimal import Decimal
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from orders.models import Order
from orders.services.lifecycle_service import OrderLifecycleService, OrderTransitionError
from payments.models import Payment
from payments.providers import get_payment_provider
from payments.providers.base import (
    CheckoutContext,
    PaymentAPIError,
    PaymentCommunicationError,
    PaymentConfigurationError,
    PaymentInvalidResponseError,
    validate_provider_confirmation,
)
from payments.services.payment_service import PaymentService
from payments.services.audit_service import PaymentAuditService

logger = logging.getLogger(__name__)


class PaymentLifecycleError(Exception):
    def __init__(self, detail, code="payment_invalid"):
        super().__init__(detail)
        self.code = code


class PaymentLifecycleService:
    ACTIVE = {"created", "initializing", "pending", "redirect_required", "processing", "unknown"}
    TERMINAL = {"completed", "failed", "cancelled", "expired", "refund_required"}

    def __init__(self, provider=None):
        self.provider = provider or get_payment_provider()

    @transaction.atomic
    def initialize(self, *, user, order_id, idempotency_key):
        order = Order.objects.select_for_update().filter(
            id=order_id, customer__user=user
        ).prefetch_related("items").first()
        if order is None:
            raise PaymentLifecycleError("Commande introuvable.", "order_not_found")
        self._validate_order(order)
        fingerprint = self._hash({"order_id": order.id, "provider": self.provider.provider_name})
        existing = Payment.objects.select_for_update().filter(
            order=order, idempotency_key=idempotency_key
        ).first()
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise PaymentLifecycleError(
                    "Cette clé a été utilisée avec une autre intention.",
                    "idempotency_conflict",
                )
            return existing, True
        completed = Payment.objects.filter(order=order, status="completed").first()
        if completed:
            return completed, True
        active = Payment.objects.filter(
            order=order, status__in=self.ACTIVE
        ).order_by("-id").first()
        if active:
            return active, True

        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            currency=order.currency,
            payment_method=self.provider.provider_name,
            provider=self.provider.provider_name,
            status="initializing",
            provider_status="",
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            order_reference="",
        )
        payment.merchant_reference = f"LOBEL-{payment.uuid.hex.upper()}"
        payment.order_reference = payment.merchant_reference
        payment.save(update_fields=["merchant_reference", "order_reference"])
        self._audit(payment, "initialization_requested", "", "initializing")

        context = CheckoutContext(
            payment=payment,
            order=order,
            amount=self.provider.format_amount(Decimal(order.total_amount)),
            currency=order.currency,
            order_reference=payment.merchant_reference,
            description=f"Commande LobelStore #{order.id}",
            customer_email=order.customer_email,
            customer_firstname=(order.delivery_recipient_name.split(" ", 1)[0] or "Client"),
            customer_lastname=(
                order.delivery_recipient_name.split(" ", 1)[1]
                if " " in order.delivery_recipient_name else "LobelStore"
            ),
            frontend_url="",
        )
        try:
            session = self.provider.create_checkout(context)
        except PaymentCommunicationError:
            payment.status = "unknown"
            payment.failure_code = "provider_communication_error"
            payment.save(update_fields=["status", "failure_code", "updated_at"])
            self._audit(payment, "initialization_ambiguous", "initializing", "unknown")
            raise
        except (PaymentAPIError, PaymentInvalidResponseError):
            payment.status = "failed"
            payment.failed_at = timezone.now()
            payment.failure_code = "provider_rejected"
            payment.save(update_fields=["status", "failed_at", "failure_code", "updated_at"])
            self._audit(payment, "initialization_failed", "initializing", "failed")
            raise

        self._validate_checkout_url(session.payment_url)
        payment.session_token = session.session_token
        payment.checkout_url = session.payment_url
        payment.status = "redirect_required"
        payment.provider_status = "pending"
        payment.initialized_at = timezone.now()
        payment.save(update_fields=[
            "session_token", "checkout_url", "status", "provider_status",
            "initialized_at", "updated_at",
        ])
        self._audit(payment, "initialization_succeeded", "initializing", "redirect_required")
        return payment, False

    @transaction.atomic
    def refresh(self, *, payment_id, user=None):
        query = Payment.objects.select_for_update().select_related("order")
        if user is not None:
            query = query.filter(order__customer__user=user)
        payment = query.filter(id=payment_id).first()
        if payment is None:
            raise PaymentLifecycleError("Paiement introuvable.", "payment_not_found")
        if payment.status in {"completed", "refund_required"}:
            return payment
        if payment.session_token:
            result = self.provider.verify_payment(
                payment.session_token, payment=payment
            )
        else:
            try:
                result = self.provider.find_payment_by_reference(
                    payment.merchant_reference, payment=payment
                )
            except PaymentConfigurationError as exc:
                self._audit(
                    payment, "reference_lookup_unavailable",
                    payment.status, payment.status,
                )
                raise PaymentLifecycleError(
                    "Recherche fournisseur par référence indisponible.",
                    "reference_lookup_unavailable",
                ) from exc
        payment.last_checked_at = timezone.now()
        payment.provider_status = (result.status or "unknown").lower()
        payment.provider_payload = PaymentAuditService.provider_evidence(result.raw)
        if payment.provider_status == "completed":
            validate_provider_confirmation(
                payment=payment, result=result, require_signature=False
            )
            before = payment.status
            payment.status = "completed"
            payment.confirmed_at = timezone.now()
            payment.external_transaction_id = result.external_transaction_id
            payment.save(update_fields=[
                "status", "provider_status", "confirmed_at",
                "external_transaction_id", "last_checked_at",
                "provider_payload", "updated_at",
            ])
            outcome = PaymentService().handle_payment_completed(payment)
            if outcome == "completed":
                self._audit(payment, "payment_confirmed", before, "completed")
            payment.refresh_from_db()
            payment.order.refresh_from_db()
        elif payment.provider_status == "notcompleted":
            before = payment.status
            payment.status = "failed"
            payment.failed_at = timezone.now()
            payment.save(update_fields=[
                "status", "provider_status", "failed_at", "last_checked_at",
                "provider_payload", "updated_at",
            ])
            self._audit(payment, "payment_failed", before, "failed")
            self._transition_order_payment_state(
                payment, Order.STATUS_PAYMENT_FAILED, "payment_failed"
            )
        else:
            before = payment.status
            payment.status = "processing"
            payment.save(update_fields=[
                "status", "provider_status", "last_checked_at",
                "provider_payload", "updated_at",
            ])
            self._audit(payment, "status_checked", before, "processing")
            self._transition_order_payment_state(
                payment, Order.STATUS_PAYMENT_PROCESSING, "payment_verification"
            )
        return payment

    @staticmethod
    def _transition_order_payment_state(payment, target_status, reason_code):
        payment.order.refresh_from_db()
        if payment.order.status == target_status:
            return
        try:
            OrderLifecycleService().transition_order(
                order=payment.order,
                target_status=target_status,
                actor=None,
                reason_code=reason_code,
                source="payment",
                payment=payment,
                metadata={"payment_id": payment.id},
            )
        except OrderTransitionError:
            logger.warning(
                "order_payment_state_not_applied payment_id=%s order_id=%s target=%s",
                payment.id, payment.order_id, target_status,
            )

    def mark_redirected(self, *, payment, user):
        if payment.order.customer.user_id != user.id:
            raise PaymentLifecycleError("Paiement introuvable.", "payment_not_found")
        if payment.status not in {"redirect_required", "processing"}:
            raise PaymentLifecycleError("Paiement non redirigeable.", "payment_not_redirectable")
        Payment.objects.filter(pk=payment.pk, redirected_at__isnull=True).update(
            redirected_at=timezone.now()
        )

    def _validate_order(self, order):
        if order.status not in {
            Order.STATUS_PENDING_PAYMENT,
            Order.STATUS_PAYMENT_PROCESSING,
            Order.STATUS_PAYMENT_FAILED,
        }:
            raise PaymentLifecycleError("Commande non payable.", "order_not_payable")
        if not order.snapshot_at or not order.items.exists():
            raise PaymentLifecycleError("Snapshot de commande incomplet.", "invalid_order_snapshot")
        if order.total_amount is None or order.total_amount <= 0:
            raise PaymentLifecycleError("Montant de commande invalide.", "invalid_amount")
        if order.currency != "XOF":
            raise PaymentLifecycleError("Devise non supportée.", "unsupported_currency")

    def _validate_checkout_url(self, value):
        try:
            parsed = urlparse(value)
        except ValueError as exc:
            raise PaymentInvalidResponseError("URL de paiement invalide.") from exc
        allowed = set(getattr(settings, "LIGDICASH_ALLOWED_CHECKOUT_HOSTS", []))
        if self.provider.provider_name == "mock" and (settings.DEBUG or settings.TESTING):
            if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
                "localhost", "127.0.0.1"
            }:
                raise PaymentInvalidResponseError("URL mock invalide.")
            return
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.hostname not in allowed
            or len(value) > 1000
        ):
            raise PaymentInvalidResponseError("URL de paiement LigdiCash refusée.")

    @staticmethod
    def _hash(payload):
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _audit(payment, event, before, after):
        PaymentAuditService.record(
            payment=payment, event_type=event,
            from_status=before, to_status=after,
        )
        logger.info(
            "[Payment] event=%s payment_id=%s order_id=%s from=%s to=%s",
            event, payment.id, payment.order_id, before, after,
        )
