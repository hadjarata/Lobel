import hashlib
import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from orders.models import Order
from orders.services.lifecycle_service import (
    ALLOWED_ORDER_TRANSITIONS,
    OrderLifecycleService,
)
from payments.models import (
    Payment,
    PaymentOperationalAlert,
    Refund,
    RefundAttempt,
)
from payments.providers import get_payment_provider
from payments.providers.base import (
    PaymentProviderError,
    RefundResult,
)
from payments.services.refund_notification_service import RefundNotificationService
from payments.services.audit_service import PaymentAuditService
from store.money import xof_integer


class RefundError(Exception):
    def __init__(self, detail, code="refund_invalid"):
        super().__init__(detail)
        self.code = code


class RefundService:
    RESERVED_STATUSES = {
        Refund.STATUS_REQUESTED,
        Refund.STATUS_PROCESSING,
        Refund.STATUS_COMPLETED,
    }

    def __init__(self, provider=None):
        self.provider = provider

    @transaction.atomic
    def request(
        self, *, payment, amount, reason, actor=None, idempotency_key
    ):
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .get(pk=payment.pk)
        )
        order = Order.objects.select_for_update().get(pk=payment.order_id)
        key = str(idempotency_key or "").strip()
        if not key or len(key) > 64:
            raise RefundError("Clé d'idempotence invalide.", "invalid_idempotency_key")
        try:
            amount = xof_integer(amount)
        except (InvalidOperation, TypeError, ValueError, ValidationError) as exc:
            raise RefundError("Montant de remboursement invalide.", "invalid_amount") from exc
        reason = str(reason or "").strip()
        if not reason:
            raise RefundError("Motif de remboursement obligatoire.", "reason_required")
        fingerprint = self._hash({
            "payment_id": payment.id,
            "amount": str(amount),
            "reason": reason,
        })
        existing = Refund.objects.filter(
            payment=payment, idempotency_key=key
        ).first()
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise RefundError(
                    "Cette clé correspond à une autre demande.",
                    "idempotency_conflict",
                )
            return existing, True
        if payment.status not in {"completed", "refund_required"}:
            raise RefundError("Paiement non remboursable.", "payment_not_refundable")
        if amount <= 0:
            raise RefundError("Le montant doit être positif.", "invalid_amount")
        reserved = Refund.objects.filter(
            payment=payment, status__in=self.RESERVED_STATUSES
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        available = Decimal(payment.amount) - reserved
        if amount > available:
            raise RefundError(
                f"Montant supérieur au solde remboursable ({available} {payment.currency}).",
                "refund_exceeds_available",
            )
        affects_order = bool(
            amount == available
            and payment.failure_code != "duplicate_payment"
        )
        refund = Refund.objects.create(
            payment=payment,
            order=order,
            amount=amount,
            currency=payment.currency,
            affects_order_status=affects_order,
            reason=reason,
            idempotency_key=key,
            request_fingerprint=fingerprint,
            requested_by=actor if getattr(actor, "is_authenticated", False) else None,
        )
        if affects_order and order.status != Order.STATUS_REFUND_PENDING:
            if Order.STATUS_REFUND_PENDING not in ALLOWED_ORDER_TRANSITIONS.get(
                order.status, set()
            ):
                raise RefundError(
                    "État de commande incompatible avec un remboursement.",
                    "order_not_refundable",
                )
            OrderLifecycleService().transition_order(
                order=order,
                target_status=Order.STATUS_REFUND_PENDING,
                actor=actor,
                reason_code="refund_requested",
                source="refund_service",
                payment=payment,
                metadata={"refund_id": refund.id, "amount": str(amount)},
            )
        RefundNotificationService.schedule(
            refund=refund, event_code="refund_requested"
        )
        PaymentAuditService.record(
            payment=payment,
            event_type="refund_requested",
            from_status=payment.status,
            to_status=payment.status,
            metadata={
                "refund_id": refund.id,
                "amount": str(refund.amount),
                "currency": refund.currency,
                "full_refund": refund.affects_order_status,
            },
        )
        return refund, False

    def process(self, *, refund_id):
        refund = self._start(refund_id=refund_id, allow_failed=True)
        if refund.status == Refund.STATUS_COMPLETED:
            return refund
        provider = self.provider or get_payment_provider()
        try:
            result = provider.create_refund(refund)
        except PaymentProviderError as exc:
            return self._fail(
                refund_id=refund.id,
                action="submit",
                code=type(exc).__name__,
                message=str(exc),
            )
        return self._apply_result(
            refund_id=refund.id, action="submit", result=result
        )

    def reconcile(self, *, refund_id):
        with transaction.atomic():
            refund = (
                Refund.objects.select_for_update()
                .select_related("payment", "order")
                .get(pk=refund_id)
            )
            if refund.status == Refund.STATUS_COMPLETED:
                return refund
            if refund.status != Refund.STATUS_PROCESSING:
                raise RefundError(
                    "Seul un remboursement en cours peut être rapproché.",
                    "refund_not_processing",
                )
        provider = self.provider or get_payment_provider()
        try:
            result = provider.verify_refund(refund)
        except PaymentProviderError as exc:
            return self._fail(
                refund_id=refund.id,
                action="reconcile",
                code=type(exc).__name__,
                message=str(exc),
            )
        return self._apply_result(
            refund_id=refund.id, action="reconcile", result=result
        )

    @transaction.atomic
    def _start(self, *, refund_id, allow_failed):
        refund = (
            Refund.objects.select_for_update()
            .select_related("payment", "order")
            .get(pk=refund_id)
        )
        payment = Payment.objects.select_for_update().get(pk=refund.payment_id)
        Order.objects.select_for_update().get(pk=refund.order_id)
        if refund.status == Refund.STATUS_COMPLETED:
            return refund
        allowed = {Refund.STATUS_REQUESTED}
        if allow_failed:
            allowed.add(Refund.STATUS_FAILED)
        if refund.status not in allowed:
            raise RefundError(
                "Remboursement déjà en cours.", "refund_already_processing"
            )
        reserved_by_others = Refund.objects.filter(
            payment=payment,
            status__in=self.RESERVED_STATUSES,
        ).exclude(pk=refund.pk).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        if refund.amount > Decimal(payment.amount) - reserved_by_others:
            raise RefundError(
                "Le solde remboursable a été attribué à une autre demande.",
                "refund_exceeds_available",
            )
        if (
            refund.status == Refund.STATUS_FAILED
            and refund.affects_order_status
            and refund.order.status == Order.STATUS_REFUND_FAILED
        ):
            OrderLifecycleService().transition_order(
                order=refund.order,
                target_status=Order.STATUS_REFUND_PENDING,
                actor=None,
                reason_code="refund_retry",
                source="refund_service",
                payment=refund.payment,
                metadata={"refund_id": refund.id},
            )
        refund.status = Refund.STATUS_PROCESSING
        refund.processing_at = refund.processing_at or timezone.now()
        refund.failure_code = ""
        refund.failure_message = ""
        refund.save(update_fields=[
            "status", "processing_at", "failure_code",
            "failure_message", "updated_at",
        ])
        RefundNotificationService.schedule(
            refund=refund, event_code="refund_processing"
        )
        return refund

    @transaction.atomic
    def _apply_result(self, *, refund_id, action, result: RefundResult):
        refund = (
            Refund.objects.select_for_update()
            .select_related("payment", "order")
            .get(pk=refund_id)
        )
        status = str(result.status or "").lower()
        if status not in {"processing", "completed", "failed"}:
            return self._fail_locked(
                refund=refund,
                action=action,
                code="invalid_provider_status",
                message=f"Statut fournisseur inconnu : {status or 'vide'}.",
                result=result,
            )
        if status == "failed":
            return self._fail_locked(
                refund=refund,
                action=action,
                code=result.response_code or "provider_refund_failed",
                message="Le fournisseur a refusé le remboursement.",
                result=result,
            )
        if status == "completed":
            try:
                self._validate_completed(refund, result)
            except RefundError as exc:
                return self._fail_locked(
                    refund=refund,
                    action=action,
                    code=exc.code,
                    message=str(exc),
                    result=result,
                )
        now = timezone.now()
        refund.provider_status = status
        refund.provider_reference = (
            result.provider_reference or refund.provider_reference
        )
        refund.last_checked_at = now
        fields = [
            "provider_status", "provider_reference",
            "last_checked_at", "updated_at",
        ]
        if status == "completed":
            refund.status = Refund.STATUS_COMPLETED
            refund.completed_at = now
            fields += ["status", "completed_at"]
        self._record_attempt(
            refund=refund, action=action, result="succeeded", provider_result=result
        )
        refund.save(update_fields=fields)
        if status == "completed":
            self._complete_business_state(refund)
            PaymentAuditService.record(
                payment=refund.payment,
                event_type="refund_completed",
                from_status=refund.payment.status,
                to_status=refund.payment.status,
                metadata={
                    "refund_id": refund.id,
                    "amount": str(refund.amount),
                    "currency": refund.currency,
                    "provider_reference": refund.provider_reference,
                },
            )
            RefundNotificationService.schedule(
                refund=refund, event_code="refund_completed"
            )
        return refund

    @transaction.atomic
    def _fail(self, *, refund_id, action, code, message):
        refund = (
            Refund.objects.select_for_update()
            .select_related("payment", "order")
            .get(pk=refund_id)
        )
        return self._fail_locked(
            refund=refund, action=action, code=code, message=message
        )

    def _fail_locked(
        self, *, refund, action, code, message, result=None
    ):
        now = timezone.now()
        refund.status = Refund.STATUS_FAILED
        refund.failed_at = now
        refund.last_checked_at = now
        refund.failure_code = str(code)[:100]
        refund.failure_message = str(message)[:500]
        if result:
            refund.provider_status = str(result.status or "")[:50]
        refund.save(update_fields=[
            "status", "failed_at", "last_checked_at", "failure_code",
            "failure_message", "provider_status", "updated_at",
        ])
        self._record_attempt(
            refund=refund,
            action=action,
            result="failed",
            provider_result=result,
            error_code=refund.failure_code,
            error_message=refund.failure_message,
        )
        if (
            refund.affects_order_status
            and refund.order.status == Order.STATUS_REFUND_PENDING
        ):
            OrderLifecycleService().transition_order(
                order=refund.order,
                target_status=Order.STATUS_REFUND_FAILED,
                actor=None,
                reason_code="provider_refund_failed",
                source="refund_service",
                payment=refund.payment,
                metadata={"refund_id": refund.id},
            )
        RefundNotificationService.schedule(
            refund=refund, event_code="refund_failed"
        )
        return refund

    @staticmethod
    def _validate_completed(refund, result):
        try:
            amount = Decimal(result.refunded_amount)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise RefundError(
                "Montant remboursé absent ou invalide.",
                "invalid_refund_confirmation",
            ) from exc
        if amount != refund.amount:
            raise RefundError(
                "Montant remboursé différent du montant demandé.",
                "refund_amount_mismatch",
            )
        if not result.currency or result.currency.upper() != refund.currency.upper():
            raise RefundError(
                "Devise remboursée incohérente.", "refund_currency_mismatch"
            )
        if not result.provider_reference:
            raise RefundError(
                "Référence fournisseur absente.", "refund_reference_missing"
            )

    @staticmethod
    def _record_attempt(
        *, refund, action, result, provider_result=None,
        error_code="", error_message="",
    ):
        sequence = refund.attempts.count() + 1
        raw = provider_result.raw if provider_result and provider_result.raw else {}
        payload_hash = hashlib.sha256(
            json.dumps(raw, sort_keys=True, default=str).encode()
        ).hexdigest() if raw else ""
        RefundAttempt.objects.create(
            refund=refund,
            sequence=sequence,
            action=action,
            result=result,
            provider_status=(
                str(provider_result.status or "")[:50] if provider_result else ""
            ),
            provider_reference=(
                str(provider_result.provider_reference or "")[:255]
                if provider_result else ""
            ),
            response_code=(
                str(provider_result.response_code or "")[:100]
                if provider_result else ""
            ),
            error_code=str(error_code)[:100],
            error_message=str(error_message)[:500],
            payload_hash=payload_hash,
            finished_at=timezone.now(),
        )

    @staticmethod
    def _complete_business_state(refund):
        if refund.affects_order_status:
            refund.order.refresh_from_db()
            if refund.order.status == Order.STATUS_REFUND_PENDING:
                OrderLifecycleService().transition_order(
                    order=refund.order,
                    target_status=Order.STATUS_REFUNDED,
                    actor=None,
                    reason_code="provider_refund_confirmed",
                    source="refund_service",
                    payment=refund.payment,
                    refund_confirmed=True,
                    metadata={
                        "refund_id": refund.id,
                        "amount": str(refund.amount),
                    },
                )
        PaymentOperationalAlert.objects.filter(
            payment=refund.payment,
            alert_type="duplicate_payment",
            status="open",
        ).update(status="resolved", resolved_at=timezone.now())

    @staticmethod
    def refundable_balance(payment):
        reserved = payment.refunds.filter(
            status__in=RefundService.RESERVED_STATUSES
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        return Decimal(payment.amount) - reserved

    @staticmethod
    def _hash(payload):
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
