from rest_framework import serializers

from products.models import ProductVariant
from users.serializers import CustomerSerializer
from .models import MAX_CART_ITEM_QUANTITY, Order, OrderItem, OrderStatusHistory


def _latest_payment(obj):
    if hasattr(obj, "_phase9_latest_payment"):
        return obj._phase9_latest_payment
    payments = list(obj.payments.all())
    obj._phase9_latest_payment = max(
        payments, key=lambda payment: payment.id, default=None
    )
    return obj._phase9_latest_payment


class OrderItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.select_related("product", "color", "size"),
        source="variant",
    )
    product_id = serializers.IntegerField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    color = serializers.CharField(source="color_name", read_only=True)
    size = serializers.CharField(source="size_name", read_only=True)
    sku = serializers.CharField(read_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(
        source="get_total", max_digits=12, decimal_places=2, read_only=True
    )
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_CART_ITEM_QUANTITY)

    class Meta:
        model = OrderItem
        fields = [
            "id", "product_id", "product_reference", "product_name", "variant_id",
            "variant_reference", "variant_name", "color", "size", "sku",
            "quantity", "unit_price", "currency", "discount_amount", "subtotal",
            "line_total", "date_added",
        ]
        read_only_fields = [
            "product_reference", "variant_reference", "variant_name", "currency",
            "discount_amount", "subtotal", "date_added",
        ]

    def validate(self, attrs):
        variant = attrs.get("variant") or getattr(self.instance, "variant", None)
        if variant is None:
            raise serializers.ValidationError({"variant_id": "Une variante est obligatoire."})
        if not variant.product.is_active:
            raise serializers.ValidationError({"variant_id": "Ce produit est inactif."})
        if not variant.is_active:
            raise serializers.ValidationError({"variant_id": "Cette variante est inactive."})
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", 1))
        if quantity > variant.stock:
            raise serializers.ValidationError({
                "quantity": f"Stock insuffisant (disponible : {variant.stock})."
            })
        return attrs


class OrderReadSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    cart_total = serializers.DecimalField(
        source="get_cart_total", max_digits=12, decimal_places=2, read_only=True
    )
    cart_items = serializers.IntegerField(source="get_cart_items", read_only=True)
    status_history = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    available_actions = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "customer", "date_ordered", "complete", "status", "paid_at",
            "transaction_id", "items", "cart_total", "cart_items",
            "snapshot_at", "customer_name", "customer_email",
            "delivery_recipient_name", "delivery_phone", "delivery_address",
            "delivery_country", "delivery_region", "delivery_city",
            "delivery_district", "delivery_street", "delivery_instructions",
            "delivery_method_code", "delivery_method_label",
            "delivery_eta_min_days", "delivery_eta_max_days",
            "billing_same_as_shipping", "billing_address", "checkout_version",
            "subtotal_amount", "shipping_amount",
            "discount_amount", "total_amount", "currency",
            "preparation_started_at", "shipped_at", "delivered_at",
            "cancelled_at", "refund_requested_at", "refunded_at",
            "stock_consumed_at", "stock_released_at", "status_history",
            "payment_processing_at", "payment_failed_at", "expired_at",
            "status_label", "timeline", "available_actions", "payment",
        ]
        read_only_fields = fields

    def get_status_history(self, obj):
        return self.get_timeline(obj)

    def get_timeline(self, obj):
        labels = {
            Order.STATUS_PENDING_PAYMENT: "Commande créée",
            Order.STATUS_PAYMENT_PROCESSING: "Paiement en vérification",
            Order.STATUS_PAYMENT_FAILED: "Paiement non confirmé",
            Order.STATUS_PAID: "Paiement confirmé",
            Order.STATUS_PREPARING: "Commande en préparation",
            Order.STATUS_SHIPPED: "Commande expédiée",
            Order.STATUS_DELIVERED: "Commande livrée",
            Order.STATUS_CANCELLED: "Commande annulée",
            Order.STATUS_EXPIRED: "Commande expirée",
            Order.STATUS_REFUND_REQUIRED: "Intervention requise",
            Order.STATUS_REFUND_PENDING: "Remboursement en cours",
            Order.STATUS_REFUNDED: "Commande remboursée",
            Order.STATUS_REFUND_FAILED: "Remboursement à vérifier",
        }
        return [
            {
                "code": event.to_status,
                "label": labels.get(event.to_status, "Statut mis à jour"),
                "occurred_at": event.created_at,
            }
            for event in obj.status_history.all()
            if event.to_status != Order.STATUS_CART
        ]

    def get_available_actions(self, obj):
        can_pay = obj.status in {
            Order.STATUS_PENDING_PAYMENT,
            Order.STATUS_PAYMENT_PROCESSING,
            Order.STATUS_PAYMENT_FAILED,
        } and not any(payment.status == "completed" for payment in obj.payments.all())
        can_cancel = obj.status in {
            Order.STATUS_PENDING_PAYMENT,
            Order.STATUS_PAYMENT_PROCESSING,
            Order.STATUS_PAYMENT_FAILED,
        } and not obj.stock_consumed_at
        return {
            "can_pay": can_pay,
            "can_cancel": can_cancel,
            "can_download_receipt": bool(
                obj.paid_at
                and obj.snapshot_at
                and obj.total_amount is not None
                and obj.status in {
                    Order.STATUS_PAID, Order.STATUS_PREPARING,
                    Order.STATUS_SHIPPED, Order.STATUS_DELIVERED,
                    Order.STATUS_REFUND_REQUIRED, Order.STATUS_REFUND_PENDING,
                    Order.STATUS_REFUNDED, Order.STATUS_REFUND_FAILED,
                }
                and any(
                    payment.status == "completed"
                    and payment.amount == obj.total_amount
                    and payment.currency == obj.currency
                    for payment in obj.payments.all()
                )
            ),
            "can_contact_support": obj.status != Order.STATUS_CART,
            "can_reorder": False,
        }

    def get_payment(self, obj):
        payment = _latest_payment(obj)
        if payment is None:
            return None
        return {
            "id": payment.id,
            "status": payment.status,
            "provider": payment.provider,
            "amount": payment.amount,
            "currency": payment.currency,
            "reference": payment.merchant_reference or payment.order_reference,
            "confirmed_at": payment.confirmed_at,
        }


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ["id", "from_status", "to_status", "created_at"]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    cart_total = serializers.DecimalField(
        source="get_cart_total", max_digits=12, decimal_places=2, read_only=True
    )
    cart_items = serializers.IntegerField(source="get_cart_items", read_only=True)
    item_count = serializers.IntegerField(source="get_cart_items", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    payment_status = serializers.SerializerMethodField()
    can_pay = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "date_ordered", "complete", "status", "cart_total",
            "cart_items", "total_amount", "currency",
            "item_count", "status_label", "payment_status", "can_pay", "can_cancel",
        ]
        read_only_fields = fields

    def get_payment_status(self, obj):
        payment = _latest_payment(obj)
        return payment.status if payment else None

    def get_can_pay(self, obj):
        return obj.status in {
            Order.STATUS_PENDING_PAYMENT,
            Order.STATUS_PAYMENT_PROCESSING,
            Order.STATUS_PAYMENT_FAILED,
        } and not any(payment.status == "completed" for payment in obj.payments.all())

    def get_can_cancel(self, obj):
        return obj.status in {
            Order.STATUS_PENDING_PAYMENT,
            Order.STATUS_PAYMENT_PROCESSING,
            Order.STATUS_PAYMENT_FAILED,
        } and not obj.stock_consumed_at


OrderSerializer = OrderReadSerializer


class CartMergeItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_CART_ITEM_QUANTITY)


class CartMergeSerializer(serializers.Serializer):
    items = CartMergeItemSerializer(many=True, allow_empty=False, max_length=50)


class CheckoutAddressSerializer(serializers.Serializer):
    recipient_name = serializers.CharField(min_length=2, max_length=200, trim_whitespace=True)
    phone = serializers.RegexField(
        r"^\+?[0-9][0-9 .-]{7,19}$",
        max_length=20,
        error_messages={"invalid": "Numéro de téléphone invalide."},
    )
    country = serializers.ChoiceField(choices=[("ML", "Mali")])
    region = serializers.CharField(max_length=100, required=False, allow_blank=True)
    city = serializers.CharField(min_length=2, max_length=100, trim_whitespace=True)
    district = serializers.CharField(max_length=150, required=False, allow_blank=True)
    street = serializers.CharField(min_length=3, max_length=250, trim_whitespace=True)
    instructions = serializers.CharField(
        max_length=500, required=False, allow_blank=True, trim_whitespace=True
    )


class CheckoutRequestSerializer(serializers.Serializer):
    shipping_address = CheckoutAddressSerializer()
    delivery_method = serializers.CharField(min_length=2, max_length=50)
    billing_same_as_shipping = serializers.BooleanField(default=True)
    billing_address = CheckoutAddressSerializer(required=False)
    checkout_version = serializers.CharField(
        min_length=64, max_length=64, required=False
    )

    def validate(self, attrs):
        if not attrs["billing_same_as_shipping"] and not attrs.get("billing_address"):
            raise serializers.ValidationError({
                "billing_address": "L'adresse de facturation est requise."
            })
        return attrs


class DeliveryOptionsRequestSerializer(serializers.Serializer):
    shipping_address = CheckoutAddressSerializer()


class OrderCancellationSerializer(serializers.Serializer):
    reason = serializers.CharField(
        min_length=3, max_length=500, trim_whitespace=True, required=False
    )
    reason_code = serializers.ChoiceField(
        choices=[("customer_request", "Customer request")], required=False
    )

    def validate(self, attrs):
        if not attrs.get("reason") and not attrs.get("reason_code"):
            raise serializers.ValidationError({"reason": "Un motif est requis."})
        return attrs
