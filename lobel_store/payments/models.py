import uuid

from django.db import models

# Create your models here.
from orders.models import (
    AppendOnlyCommercialQuerySet, CommercialDataDeletionError, Order,
    ProtectedCommercialQuerySet,
)
from store.money import validate_xof_integer


class Payment(models.Model):
    objects = ProtectedCommercialQuerySet.as_manager()
    PROVIDERS = (
        ('manual', 'Manual'),
        ('mock', 'Mock'),
        ('ligdicash', 'LigdiCash'),
    )

    PAYMENT_METHODS = (
        ('card', 'Card'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
        ('mock', 'Mock'),
        ('ligdicash', 'LigdiCash'),
    )

    STATUS_CHOICES = (
        ('created', 'Created'),
        ('initializing', 'Initializing'),
        ('pending', 'Pending'),
        ('redirect_required', 'Redirect required'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('refund_required', 'Refund required'),
        ('unknown', 'Unknown'),
    )

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[validate_xof_integer]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider = models.CharField(max_length=30, choices=PROVIDERS, default='manual')
    session_token = models.CharField(max_length=255, blank=True, null=True, unique=True)
    order_reference = models.CharField(max_length=255, blank=True)
    external_transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    currency = models.CharField(max_length=3, default='XOF')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Deprecated compatibility field: historically this stored creation time,
    # not the instant the provider confirmed payment.
    date_paid = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    merchant_reference = models.CharField(max_length=64, unique=True, null=True, blank=True)
    idempotency_key = models.CharField(max_length=64, blank=True)
    request_fingerprint = models.CharField(max_length=64, blank=True)
    provider_status = models.CharField(max_length=50, blank=True)
    checkout_url = models.URLField(max_length=1000, blank=True)
    initialized_at = models.DateTimeField(null=True, blank=True)
    redirected_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=100, blank=True)
    failure_message = models.CharField(max_length=500, blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="unique_payment_key_per_order",
            ),
            models.CheckConstraint(
                condition=models.Q(amount=models.functions.Floor("amount")),
                name="payment_amount_xof_integer",
            ),
        ]

    def __str__(self):
        return f"{self.status} - {self.amount} for Order {self.order.id}"

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Un paiement ne peut pas être supprimé."
        )


class PaymentAuditEvent(models.Model):
    objects = ProtectedCommercialQuerySet.as_manager()
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="audit_events"
    )
    event_type = models.CharField(max_length=50)
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Un événement d'audit de paiement ne peut pas être supprimé."
        )


class PaymentOperationalAlert(models.Model):
    objects = ProtectedCommercialQuerySet.as_manager()

    SEVERITY_CHOICES = (("warning", "Warning"), ("critical", "Critical"))
    STATUS_CHOICES = (("open", "Open"), ("resolved", "Resolved"))

    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="operational_alerts"
    )
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="payment_alerts"
    )
    alert_type = models.CharField(max_length=50)
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default="critical"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open"
    )
    message = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "alert_type"],
                name="unique_payment_operational_alert",
            ),
        ]
        indexes = [
            models.Index(
                fields=["status", "severity", "created_at"],
                name="payment_alert_queue_idx",
            ),
        ]

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Une alerte opérationnelle de paiement ne peut pas être supprimée."
        )


class Refund(models.Model):
    objects = ProtectedCommercialQuerySet.as_manager()

    STATUS_REQUESTED = "requested"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_REQUESTED, "Requested"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="refunds"
    )
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="refunds"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_xof_integer]
    )
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_REQUESTED
    )
    affects_order_status = models.BooleanField(default=False)
    reason = models.CharField(max_length=500)
    idempotency_key = models.CharField(max_length=64)
    request_fingerprint = models.CharField(max_length=64)
    provider_reference = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    provider_status = models.CharField(max_length=50, blank=True)
    requested_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    processing_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=100, blank=True)
    failure_message = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="refund_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["payment", "idempotency_key"],
                name="unique_refund_key_per_payment",
            ),
            models.CheckConstraint(
                condition=models.Q(amount=models.functions.Floor("amount")),
                name="refund_amount_xof_integer",
            ),
        ]
        indexes = [
            models.Index(
                fields=["status", "requested_at"],
                name="refund_reconcile_queue_idx",
            ),
        ]

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Un remboursement ne peut pas être supprimé."
        )


class RefundAttempt(models.Model):
    objects = AppendOnlyCommercialQuerySet.as_manager()

    ACTION_CHOICES = (
        ("submit", "Submit"),
        ("reconcile", "Reconcile"),
    )
    RESULT_CHOICES = (
        ("started", "Started"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    )

    refund = models.ForeignKey(
        Refund, on_delete=models.PROTECT, related_name="attempts"
    )
    sequence = models.PositiveIntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    result = models.CharField(
        max_length=20, choices=RESULT_CHOICES, default="started"
    )
    provider_status = models.CharField(max_length=50, blank=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    response_code = models.CharField(max_length=100, blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    payload_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["refund_id", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["refund", "sequence"],
                name="unique_refund_attempt_sequence",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise CommercialDataDeletionError(
                "Une tentative de remboursement est append-only."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Une tentative de remboursement ne peut pas être supprimée."
        )


class RefundNotificationReceipt(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    refund = models.ForeignKey(
        Refund, on_delete=models.PROTECT, related_name="notification_receipts"
    )
    event_code = models.CharField(max_length=50)
    recipient_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["refund", "event_code"],
                name="unique_refund_notification_event",
            ),
        ]

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Une notification de remboursement ne peut pas être supprimée."
        )


class PaymentWebhookEvent(models.Model):
    objects = ProtectedCommercialQuerySet.as_manager()
    deduplication_key = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    session_token = models.CharField(max_length=255, blank=True)
    payload_hash = models.CharField(max_length=64)
    signature_verified = models.BooleanField(default=False)
    authentication_method = models.CharField(max_length=50, blank=True)
    provider_event_id = models.CharField(max_length=255, blank=True)
    source_ip_hash = models.CharField(max_length=64, blank=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_events',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.deduplication_key}"

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Une preuve de paiement ne peut pas être supprimée."
        )
