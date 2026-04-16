from rest_framework import serializers
from .models import Order, OrderItem
from users.serializers import CustomerSerializer
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()  # nested product info

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'date_added']

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    items = OrderItemSerializer(many=True)  # récupère tous les items liés à la commande

    class Meta:
        model = Order
        fields = ['id', 'customer', 'date_ordered', 'complete', 'transaction_id', 'items']