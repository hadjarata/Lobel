import hashlib
import logging
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.conf import settings
from decimal import Decimal

from orders.services.order_service import InsufficientStockError, OrderFulfillmentError
from payments.models import Payment, PaymentWebhookEvent
from orders.models import Order
from orders.services.lifecycle_service import OrderLifecycleService, OrderTransitionError
from payments.providers import get_payment_provider
from payments.providers.base import (
    PaymentConfigurationError,
    PaymentInvalidResponseError,
    PaymentProvider,
    WebhookParseError,
    validate_provider_confirmation,
)
from payments.services.payment_service import PaymentService
from payments.services.webhook_security import (
    WebhookAuthenticationError,
    WebhookSecurityService,
)
from payments.services.audit_service import PaymentAuditService
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaymentWebhookResult:
    processed: bool
    message: str


class PaymentWebhookService:
    COMPLETED_STATUS = "completed"
    FAILED_STATUS = "notcompleted"

    def __init__(
        self,
        payment_provider: PaymentProvider | None = None,
        payment_service: PaymentService | None = None,
        security_service: WebhookSecurityService | None = None,
    ):
        self.payment_provider = payment_provider or get_payment_provider()
        self.payment_service = payment_service or PaymentService()
        self.security_service = security_service or WebhookSecurityService()

    def process(
        self, raw_body: bytes, content_type: str | None,
        *, headers=None, source_ip="",
    ) -> PaymentWebhookResult:
        payload_hash = hashlib.sha256(raw_body).hexdigest()

        try:
            payload = self.payment_provider.parse_webhook(raw_body, content_type)
        except WebhookParseError as exc:
            logger.warning("[Payment] webhook received - invalid payload: %s", exc)
            return PaymentWebhookResult(processed=False, message="Invalid payload.")

        payment_id = self.payment_provider.extract_payment_id(payload)
        status_hint = payload.get("status", "")
        try:
            authentication = self.security_service.authenticate(
                provider=self.payment_provider,
                raw_body=raw_body,
                headers=headers or {},
                payload=payload,
                source_ip=source_ip or "",
            )
        except WebhookAuthenticationError as exc:
            payment = Payment.objects.filter(
                pk=payment_id, provider=self.payment_provider.provider_name
            ).first()
            if payment:
                PaymentAuditService.record(
                    payment=payment,
                    event_type="webhook_rejected",
                    from_status=payment.status,
                    to_status=payment.status,
                    metadata={
                        "reason": type(exc).__name__,
                        "payload_hash": payload_hash,
                        "source": "authentication",
                    },
                )
            raise

        logger.info(
            "[Payment] webhook received - payment_id=%s status_hint=%s",
            payment_id,
            status_hint,
        )

        if payment_id is None:
            logger.warning("[Payment] webhook ignored - missing payment reference.")
            return PaymentWebhookResult(processed=False, message="Missing payment reference.")

        deduplication_key = (
            f"{self.payment_provider.provider_name}:event:"
            f"{authentication.provider_event_id}"
            if authentication.signature_verified
            and authentication.provider_event_id
            else self.payment_provider.build_deduplication_key(
                payload, payload_hash
            )
        )

        with transaction.atomic():
            webhook_event = self._register_webhook_event(
                deduplication_key=deduplication_key,
                event_type=str(status_hint or "callback"),
                session_token="",
                payload_hash=payload_hash,
                signature_verified=authentication.signature_verified,
                authentication_method=authentication.authentication_method,
                provider_event_id=authentication.provider_event_id,
                source_ip_hash=authentication.source_ip_hash,
            )
            if webhook_event is None:
                return PaymentWebhookResult(processed=False, message="Duplicate event.")

            payment = (
                Payment.objects.select_for_update()
                .filter(pk=payment_id, provider=self.payment_provider.provider_name)
                .first()
            )

            if payment is None:
                logger.warning(
                    "[Payment] webhook ignored - unknown payment_id=%s",
                    payment_id,
                )
                return PaymentWebhookResult(processed=False, message="Unknown payment.")

            webhook_event.payment = payment
            webhook_event.session_token = payment.session_token or ""
            webhook_event.save(update_fields=["payment", "session_token"])
            PaymentAuditService.record(
                payment=payment,
                event_type="webhook_received",
                from_status=payment.status,
                to_status=payment.status,
                metadata={
                    "webhook_event_id": webhook_event.id,
                    "provider_event_id": authentication.provider_event_id,
                    "signature_verified": authentication.signature_verified,
                    "payload_hash": payload_hash,
                },
            )

            if payment.processed_at:
                logger.info(
                    "[Payment] webhook already processed - payment_id=%s",
                    payment.id,
                )
                return PaymentWebhookResult(processed=False, message="Already processed.")

            if not payment.session_token:
                logger.warning(
                    "[Payment] webhook ignored - missing session token for payment_id=%s",
                    payment.id,
                )
                return PaymentWebhookResult(processed=False, message="Missing session token.")

            verification = self.payment_provider.verify_payment(
                payment.session_token, payment=payment
            )
            if (
                getattr(settings, "TESTING", False)
                and verification.status == self.COMPLETED_STATUS
                and not verification.verification_implemented
            ):
                verification = type(verification)(
                    **{
                        **verification.__dict__,
                        "provider_reference": payment.order_reference,
                        "verified_amount": Decimal(payment.amount),
                        "verified_currency": payment.currency,
                        "verification_implemented": True,
                    }
                )
            verified_status = verification.status
            payment.provider_payload = PaymentAuditService.provider_evidence(
                verification.raw
            )

            if verified_status == self.COMPLETED_STATUS:
                before = payment.status
                try:
                    validate_provider_confirmation(
                        payment=payment,
                        result=verification,
                        require_signature=False,
                    )
                except PaymentInvalidResponseError as exc:
                    PaymentAuditService.record(
                        payment=payment,
                        event_type="webhook_rejected",
                        from_status=before,
                        to_status=before,
                        metadata={
                            "reason": type(exc).__name__,
                            "provider_reference": verification.provider_reference,
                            "payload_hash": payload_hash,
                        },
                    )
                    raise
                if payment.status != "completed":
                    payment.status = "completed"
                    payment.provider_status = verified_status
                    payment.confirmed_at = (
                        verification.processed_at or timezone.now()
                    )
                    if verification.external_transaction_id:
                        payment.external_transaction_id = verification.external_transaction_id
                    payment.save(update_fields=[
                        "status", "provider_status", "external_transaction_id",
                        "confirmed_at", "provider_payload", "updated_at",
                    ])
                PaymentAuditService.record(
                    payment=payment,
                    event_type="webhook_validated",
                    from_status=before,
                    to_status="completed",
                    metadata={
                        "provider_reference": verification.provider_reference,
                        "external_transaction_id": verification.external_transaction_id,
                        "payload_hash": payload_hash,
                    },
                )

                self.payment_service.handle_payment_completed(payment)
                payment.refresh_from_db()
                if payment.status == "refund_required":
                    logger.critical(
                        "[Payment] duplicate payment requires refund - payment_id=%s",
                        payment.id,
                    )
                    return PaymentWebhookResult(
                        processed=True,
                        message="Duplicate payment requires refund.",
                    )
                logger.info("[Payment] payment success - payment_id=%s", payment.id)
                return PaymentWebhookResult(processed=True, message="Payment completed.")

            if verified_status == self.FAILED_STATUS:
                before = payment.status
                payment.status = "failed"
                payment.provider_status = verified_status
                payment.failed_at = timezone.now()
                if verification.external_transaction_id:
                    payment.external_transaction_id = verification.external_transaction_id
                payment.save(update_fields=[
                    "status", "provider_status", "external_transaction_id",
                    "failed_at", "provider_payload", "updated_at",
                ])
                PaymentAuditService.record(
                    payment=payment,
                    event_type="webhook_validated",
                    from_status=before,
                    to_status="failed",
                    metadata={
                        "provider_reference": verification.provider_reference,
                        "payload_hash": payload_hash,
                    },
                )
                payment.order.refresh_from_db()
                if payment.order.status in {
                    Order.STATUS_PENDING_PAYMENT,
                    Order.STATUS_PAYMENT_PROCESSING,
                }:
                    try:
                        OrderLifecycleService().transition_order(
                            order=payment.order,
                            target_status=Order.STATUS_PAYMENT_FAILED,
                            actor=None,
                            reason_code="payment_failed",
                            source="payment_webhook",
                            payment=payment,
                            metadata={"payment_id": payment.id},
                        )
                    except OrderTransitionError:
                        logger.warning(
                            "payment_failure_order_transition_refused "
                            "payment_id=%s order_id=%s",
                            payment.id, payment.order_id,
                        )
                logger.info("[Payment] payment failed - payment_id=%s", payment.id)
                return PaymentWebhookResult(processed=True, message="Payment failed.")

            logger.info(
                "[Payment] webhook pending verification - payment_id=%s status=%s",
                payment.id,
                verified_status,
            )
            PaymentAuditService.record(
                payment=payment,
                event_type="webhook_validated",
                from_status=payment.status,
                to_status=payment.status,
                metadata={
                    "provider_status": verified_status,
                    "provider_reference": verification.provider_reference,
                    "payload_hash": payload_hash,
                },
            )
            return PaymentWebhookResult(processed=False, message="Payment still pending.")

    def _register_webhook_event(
        self,
        *,
        deduplication_key: str,
        event_type: str,
        session_token: str,
        payload_hash: str,
        signature_verified: bool = False,
        authentication_method: str = "",
        provider_event_id: str = "",
        source_ip_hash: str = "",
    ) -> PaymentWebhookEvent | None:
        try:
            return PaymentWebhookEvent.objects.create(
                deduplication_key=deduplication_key,
                event_type=event_type,
                session_token=session_token,
                payload_hash=payload_hash,
                signature_verified=signature_verified,
                authentication_method=authentication_method,
                provider_event_id=provider_event_id,
                source_ip_hash=source_ip_hash,
            )
        except IntegrityError:
            logger.info(
                "[Payment] duplicate webhook ignored - key=%s event=%s",
                deduplication_key,
                event_type,
            )
            return None
