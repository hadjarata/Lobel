from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from users.models import Customer
from products.models import Product, ProductVariant

MAX_CART_ITEM_QUANTITY = 99


class CommercialDataDeletionError(ValidationError):
    pass


class ProtectedCommercialQuerySet(models.QuerySet):
    def delete(self):
        raise CommercialDataDeletionError(
            "La suppression des données commerciales est interdite."
        )


class AppendOnlyCommercialQuerySet(ProtectedCommercialQuerySet):
    def update(self, **kwargs):
        raise CommercialDataDeletionError(
            "L'historique commercial est append-only."
        )


class Order(models.Model):
    objects = ProtectedCommercialQuerySet.as_manager()
    STATUS_CART = 'cart'
    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_PAYMENT_PROCESSING = 'payment_processing'
    STATUS_PAYMENT_FAILED = 'payment_failed'
    STATUS_PAID = 'paid'
    STATUS_PREPARING = 'preparing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_EXPIRED = 'expired'
    STATUS_REFUND_REQUIRED = 'refund_required'
    STATUS_REFUND_PENDING = 'refund_pending'
    STATUS_REFUNDED = 'refunded'
    STATUS_REFUND_FAILED = 'refund_failed'
    # Compatibility name retained for clients/tests from phases 1-4.
    STATUS_PENDING = STATUS_CART
    STATUS_FAILED = STATUS_REFUND_FAILED

    STATUS_CHOICES = (
        (STATUS_CART, 'Cart'),
        (STATUS_PENDING_PAYMENT, 'Pending payment'),
        (STATUS_PAYMENT_PROCESSING, 'Payment processing'),
        (STATUS_PAYMENT_FAILED, 'Payment failed'),
        (STATUS_PAID, 'Paid'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_REFUND_REQUIRED, 'Refund required'),
        (STATUS_REFUND_PENDING, 'Refund pending'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_REFUND_FAILED, 'Refund failed'),
    )

    TERMINAL_STATUSES = frozenset({
        STATUS_DELIVERED, STATUS_CANCELLED, STATUS_EXPIRED, STATUS_REFUNDED,
    })

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='orders')
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CART)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_processing_at = models.DateTimeField(null=True, blank=True)
    payment_failed_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    snapshot_at = models.DateTimeField(null=True, blank=True)
    customer_name = models.CharField(max_length=300, blank=True)
    customer_email = models.EmailField(blank=True)
    delivery_recipient_name = models.CharField(max_length=300, blank=True)
    delivery_phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    delivery_country = models.CharField(max_length=3, blank=True)
    delivery_region = models.CharField(max_length=100, blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_district = models.CharField(max_length=150, blank=True)
    delivery_street = models.CharField(max_length=250, blank=True)
    delivery_instructions = models.CharField(max_length=500, blank=True)
    delivery_method_code = models.CharField(max_length=50, blank=True)
    delivery_method_label = models.CharField(max_length=100, blank=True)
    delivery_eta_min_days = models.PositiveSmallIntegerField(null=True, blank=True)
    delivery_eta_max_days = models.PositiveSmallIntegerField(null=True, blank=True)
    billing_same_as_shipping = models.BooleanField(default=True)
    billing_address = models.TextField(blank=True)
    checkout_version = models.CharField(max_length=64, blank=True)
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="XOF")
    preparation_started_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_requested_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    stock_consumed_at = models.DateTimeField(null=True, blank=True)
    stock_released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(status="cart"),
                name="unique_active_cart_per_customer",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal_amount__isnull=True) | models.Q(subtotal_amount__gte=0),
                name="order_subtotal_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(shipping_amount__gte=0),
                name="order_shipping_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(discount_amount__gte=0),
                name="order_discount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(total_amount__isnull=True) | models.Q(total_amount__gte=0),
                name="order_total_non_negative",
            ),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.customer}"

    @property
    def get_cart_total(self):
        if self.snapshot_at and self.total_amount is not None:
            return self.total_amount
        items = self.items.all()
        return sum([item.get_total for item in items])

    @property
    def get_cart_items(self):
        items = self.items.all()
        return sum([item.quantity for item in items])

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if (
                previous and previous.status != self.status
                and not getattr(self, "_status_transition_allowed", False)
            ):
                raise ValidationError(
                    "Le statut doit être modifié par OrderLifecycleService."
                )
            if previous and previous.snapshot_at:
                immutable = (
                    "snapshot_at", "customer_name", "customer_email",
                    "delivery_recipient_name", "delivery_phone", "delivery_address",
                    "delivery_country", "delivery_region", "delivery_city",
                    "delivery_district", "delivery_street", "delivery_instructions",
                    "delivery_method_code", "delivery_method_label",
                    "delivery_eta_min_days", "delivery_eta_max_days",
                    "billing_same_as_shipping", "billing_address", "checkout_version",
                    "subtotal_amount", "shipping_amount",
                    "discount_amount", "total_amount", "currency",
                )
                if any(getattr(self, field) != getattr(previous, field) for field in immutable):
                    raise ValidationError("Les snapshots d'une commande figée sont immuables.")
        super().save(*args, **kwargs)

    def _apply_status_transition(self, target_status):
        self.status = target_status
        self._status_transition_allowed = True

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Une commande ne peut pas être supprimée."
        )


class OrderStatusHistory(models.Model):
    objects = AppendOnlyCommercialQuerySet.as_manager()
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="status_history"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    actor = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    actor_role_snapshot = models.CharField(max_length=30, blank=True)
    reason_code = models.CharField(max_length=50, blank=True)
    reason_note = models.TextField(blank=True)
    source = models.CharField(max_length=50, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(from_status=models.F("to_status")),
                name="order_history_status_changed",
            ),
        ]

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "L'historique commercial ne peut pas être supprimé."
        )

    def save(self, *args, **kwargs):
        if self.pk:
            raise CommercialDataDeletionError(
                "L'historique commercial est append-only."
            )
        super().save(*args, **kwargs)


class OrderNotificationReceipt(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    )

    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="notification_receipts"
    )
    event_code = models.CharField(max_length=50)
    channel = models.CharField(max_length=20, default="email")
    recipient_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "event_code", "channel"],
                name="unique_order_notification_event_channel",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"], name="order_notif_status_idx"),
        ]

    def delete(self, *args, **kwargs):
        raise CommercialDataDeletionError(
            "Les reçus de notification ne peuvent pas être supprimés."
        )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    product_name = models.CharField(max_length=200, blank=True)
    color_name = models.CharField(max_length=50, blank=True)
    size_name = models.CharField(max_length=20, blank=True)
    sku = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    product_reference = models.BigIntegerField(null=True, blank=True)
    variant_reference = models.BigIntegerField(null=True, blank=True)
    variant_name = models.CharField(max_length=150, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_valid",
            ),
            models.UniqueConstraint(
                fields=["order", "variant"],
                condition=models.Q(variant__isnull=False),
                name="unique_variant_per_cart",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__isnull=True) | models.Q(unit_price__gte=0),
                name="order_item_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(discount_amount__gte=0),
                name="order_item_discount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal__isnull=True) | models.Q(subtotal__gte=0),
                name="order_item_subtotal_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Produit supprimé'}"

    def save(self, *args, **kwargs):
        previous = type(self).objects.filter(pk=self.pk).first() if self.pk else None
        if previous and previous.order.snapshot_at:
            immutable = (
                "product_id", "variant_id", "quantity", "product_reference",
                "variant_reference", "product_name", "variant_name", "color_name",
                "size_name", "sku", "unit_price", "currency",
                "discount_amount", "subtotal",
            )
            if any(getattr(self, field) != getattr(previous, field) for field in immutable):
                raise ValidationError("Une ligne de commande figée est immuable.")
        if self.variant_id is None and self.product_id:
            variants = list(self.product.variants.all()[:2])
            if len(variants) == 1:
                self.variant = variants[0]
        if self.variant_id:
            if self.product_id and self.variant.product_id != self.product_id:
                raise ValidationError("La variante n'appartient pas au produit.")
            self.product = self.variant.product
            self.product_name = self.product_name or self.product.name
            self.color_name = self.color_name or (
                self.variant.color.name if self.variant.color else ""
            )
            self.size_name = self.size_name or (
                self.variant.size.name if self.variant.size else ""
            )
            self.sku = self.sku or self.variant.sku
            if self.unit_price is None:
                self.unit_price = self.variant.effective_price
            self.product_reference = self.product_reference or self.product_id
            self.variant_reference = self.variant_reference or self.variant_id
            self.variant_name = self.variant_name or " / ".join(
                value for value in (self.color_name, self.size_name) if value
            )
        super().save(*args, **kwargs)

    @property
    def get_total(self):
        if self.subtotal is not None:
            return self.subtotal
        price = self.unit_price
        if price is None and self.variant_id:
            price = self.variant.effective_price
        if price is None and self.product:
            price = self.product.price
        return (price or 0) * self.quantity


class CartMergeReceipt(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="cart_merge_receipts"
    )
    idempotency_key = models.CharField(max_length=64)
    request_fingerprint = models.CharField(max_length=64)
    response_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "idempotency_key"],
                name="unique_cart_merge_key_per_customer",
            ),
        ]


class CheckoutCreationReceipt(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="checkout_creation_receipts"
    )
    idempotency_key = models.CharField(max_length=64)
    request_fingerprint = models.CharField(max_length=64)
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="checkout_creation_receipts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "idempotency_key"],
                name="unique_checkout_key_per_customer",
            ),
        ]
