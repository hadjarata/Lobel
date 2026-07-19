from rest_framework import serializers

from products.models import ProductVariant
from users.serializers import CustomerSerializer
from .models import MAX_CART_ITEM_QUANTITY, Order, OrderItem, OrderStatusHistory


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

    class Meta:
        model = Order
        fields = [
            "id", "customer", "date_ordered", "complete", "status", "paid_at",
            "transaction_id", "items", "cart_total", "cart_items",
            "snapshot_at", "customer_name", "customer_email",
            "delivery_recipient_name", "delivery_phone", "delivery_address",
            "delivery_country", "subtotal_amount", "shipping_amount",
            "discount_amount", "total_amount", "currency",
            "preparation_started_at", "shipped_at", "delivered_at",
            "cancelled_at", "refund_requested_at", "refunded_at",
            "stock_consumed_at", "stock_released_at", "status_history",
        ]
        read_only_fields = fields

    def get_status_history(self, obj):
        return OrderStatusHistorySerializer(
            obj.status_history.all(), many=True
        ).data


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    actor_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            "id", "from_status", "to_status", "actor_id",
            "actor_role_snapshot", "reason_code", "reason_note",
            "metadata", "created_at",
        ]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    cart_total = serializers.DecimalField(
        source="get_cart_total", max_digits=12, decimal_places=2, read_only=True
    )
    cart_items = serializers.IntegerField(source="get_cart_items", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "date_ordered", "complete", "status", "cart_total",
            "cart_items", "total_amount", "currency",
        ]
        read_only_fields = fields


OrderSerializer = OrderReadSerializer
