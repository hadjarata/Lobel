import uuid

from django.db import models

# Create your models here.
from orders.models import (
    CommercialDataDeletionError, Order, ProtectedCommercialQuerySet,
)


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
        ('unknown', 'Unknown'),
    )

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider = models.CharField(max_length=30, choices=PROVIDERS, default='manual')
    session_token = models.CharField(max_length=255, blank=True, null=True, unique=True)
    order_reference = models.CharField(max_length=255, blank=True)
    external_transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    currency = models.CharField(max_length=3, default='XOF')
    processed_at = models.DateTimeField(null=True, blank=True)
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


class PaymentWebhookEvent(models.Model):
    objects = ProtectedCommercialQuerySet.as_manager()
    deduplication_key = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    session_token = models.CharField(max_length=255, blank=True)
    payload_hash = models.CharField(max_length=64)
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
