from rest_framework import serializers
from .models import Payment
from orders.serializers import OrderSerializer


class PaymentOrderSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    date_ordered = serializers.DateTimeField()


class PaymentListSerializer(serializers.ModelSerializer):
    order = PaymentOrderSummarySerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "order", "amount", "payment_method", "status", "provider",
            "currency", "processed_at", "date_paid",
        ]
        read_only_fields = fields

class PaymentReadSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)  # nested order info

    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'amount',
            'payment_method',
            'status',
            'provider',
            'session_token',
            'order_reference',
            'external_transaction_id',
            'currency',
            'processed_at',
            'date_paid',
        ]
        read_only_fields = fields


# Backwards-compatible import used by existing views and tests.
PaymentSerializer = PaymentReadSerializer
