from rest_framework import serializers
from .models import Payment
from orders.serializers import OrderSerializer

class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer()  # nested order info

    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'payment_method', 'status', 'date_paid']