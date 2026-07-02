from django.db import models

# Create your models here.
from orders.models import Order


class Payment(models.Model):
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
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
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

    def __str__(self):
        return f"{self.status} - {self.amount} for Order {self.order.id}"


class PaymentWebhookEvent(models.Model):
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