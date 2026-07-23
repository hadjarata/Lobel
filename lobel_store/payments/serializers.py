from rest_framework import serializers
from .models import Payment, Refund
from orders.serializers import OrderSerializer


class PaymentOrderSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    date_ordered = serializers.DateTimeField()


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            "id", "uuid", "amount", "currency", "status", "reason",
            "provider_reference", "requested_at", "processing_at",
            "completed_at", "failed_at", "failure_code",
        ]
        read_only_fields = fields


class PaymentListSerializer(serializers.ModelSerializer):
    order = PaymentOrderSummarySerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "order", "amount", "payment_method", "status", "provider",
            "currency", "created_at", "processed_at", "date_paid",
        ]
        read_only_fields = fields

class PaymentReadSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)  # nested order info
    refunds = RefundSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'uuid',
            'order',
            'amount',
            'payment_method',
            'status',
            'provider',
            'order_reference',
            'merchant_reference',
            'external_transaction_id',
            'currency',
            'provider_status',
            'initialized_at',
            'redirected_at',
            'confirmed_at',
            'failed_at',
            'cancelled_at',
            'expired_at',
            'last_checked_at',
            'processed_at',
            'created_at',
            'date_paid',
            'refunds',
        ]
        read_only_fields = fields


# Backwards-compatible import used by existing views and tests.
PaymentSerializer = PaymentReadSerializer


class PaymentInitializeSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)


class PaymentSessionSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    status = serializers.CharField()
    provider = serializers.CharField()
    checkout_url = serializers.URLField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    replayed = serializers.BooleanField()
