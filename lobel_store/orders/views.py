from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from users.models import Customer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if not user or not user.is_authenticated:
            raise ValidationError({"detail": "Authentication required."})

        customer, _ = Customer.objects.get_or_create(user=user)
        order = Order.objects.filter(customer=customer, complete=False).first()

        if order is None:
            order = Order.objects.create(customer=customer, complete=False)

        serializer.save(order=order)
