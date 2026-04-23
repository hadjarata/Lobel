from rest_framework import serializers
from .models import Order, OrderItem
from users.serializers import CustomerSerializer
from products.models import Product
from products.serializers import ProductSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    # Pour affichage
    product = ProductSerializer(read_only=True)

    # Pour écriture (ajout panier)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'date_added']


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    # 🔥 Ajout des totaux
    cart_total = serializers.FloatField(source='get_cart_total', read_only=True)
    cart_items = serializers.IntegerField(source='get_cart_items', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer',
            'date_ordered',
            'complete',
            'transaction_id',
            'items',
            'cart_total',
            'cart_items'
        ]