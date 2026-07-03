from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .services.cart_service import CartService

cart_service = CartService()

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Order.objects.none()

        queryset = Order.objects.filter(customer__user=self.request.user)

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        complete_param = self.request.query_params.get("complete")
        if complete_param is not None:
            if complete_param.lower() in ("true", "1"):
                queryset = queryset.filter(complete=True)
            elif complete_param.lower() in ("false", "0"):
                queryset = queryset.filter(complete=False)

        return queryset.prefetch_related('items__product__media_files')

    @action(detail=False, methods=["get"], url_path="cart")
    def cart(self, request):
        """Retourne le panier actif (commande non finalisée) du client connecté."""
        customer = cart_service.get_customer(request.user)
        if customer is None:
            return Response(cart_service.empty_cart_payload())

        order = cart_service.get_active_cart(customer, prefetch=True, create=False)
        cart_service.log_cart_state("GET /cart/", request.user, order)

        if order is None:
            return Response(cart_service.empty_cart_payload())

        return Response(OrderSerializer(order, context={'request': request}).data)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return OrderItem.objects.none()
        return OrderItem.objects.filter(order__customer__user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user

        if not user or not user.is_authenticated:
            raise ValidationError({"detail": "Authentication required."})

        customer = cart_service.get_customer(user)
        order = cart_service.get_active_cart(customer, prefetch=False, create=True)

        product = serializer.validated_data.get("product")
        quantity = serializer.validated_data.get("quantity", 1)
        cart_service.log_cart_state(
            f"Add Product product_id={getattr(product, 'id', None)} quantity={quantity}",
            user,
            order,
        )

        serializer.save(order=order)
