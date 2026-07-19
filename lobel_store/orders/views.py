from rest_framework import permissions, viewsets
from django.db.models import Prefetch
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, OrderListSerializer
from .services.cart_service import CartError, CartService
from .services.lifecycle_service import OrderLifecycleService, OrderTransitionError
from .permissions import IsOrderOwner

cart_service = CartService()
lifecycle_service = OrderLifecycleService()

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwner]

    def get_serializer_class(self):
        return OrderListSerializer if self.action == "list" else OrderSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Order.objects.none()

        queryset = Order.objects.all() if self.request.user.is_staff else Order.objects.filter(
            customer__user=self.request.user
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        complete_param = self.request.query_params.get("complete")
        if complete_param is not None:
            if complete_param.lower() in ("true", "1"):
                queryset = queryset.filter(complete=True)
            elif complete_param.lower() in ("false", "0"):
                queryset = queryset.filter(complete=False)

        queryset = queryset.select_related("customer__user").order_by("-date_ordered", "-id")
        items = OrderItem.objects.select_related(
            "product", "variant__product", "variant__color", "variant__size"
        ).order_by("id")
        if self.action == "list":
            return queryset.prefetch_related(Prefetch("items", queryset=items))
        return queryset.prefetch_related(Prefetch("items", queryset=items), "status_history")

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

    def _transition(self, request, target_status, *, require_reason=False):
        order = self.get_object()
        reason_code = str(request.data.get("reason_code", "")).strip()
        if require_reason and not reason_code:
            return Response(
                {"code": "invalid_reason", "detail": "reason_code requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            order, changed = lifecycle_service.transition_order(
                order=order,
                target_status=target_status,
                actor=request.user,
                reason_code=reason_code,
                reason_note=request.data.get("reason_note", ""),
            )
        except OrderTransitionError as exc:
            http_status = (
                status.HTTP_403_FORBIDDEN if exc.code == "forbidden"
                else status.HTTP_409_CONFLICT
            )
            return Response(
                {"code": exc.code, "detail": str(exc)}, status=http_status
            )
        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(
            request, Order.STATUS_CANCELLED, require_reason=True
        )

    @action(detail=True, methods=["post"])
    def prepare(self, request, pk=None):
        return self._transition(request, Order.STATUS_PREPARING)

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        return self._transition(request, Order.STATUS_SHIPPED)

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        return self._transition(request, Order.STATUS_DELIVERED)

    @action(detail=True, methods=["post"], url_path="request-refund")
    def request_refund(self, request, pk=None):
        return self._transition(
            request, Order.STATUS_REFUND_PENDING, require_reason=True
        )


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return OrderItem.objects.none()
        return OrderItem.objects.filter(
            order__customer__user=self.request.user
        ).select_related(
            "order", "product", "variant__product", "variant__color", "variant__size"
        ).order_by("id")

    def create(self, request, *args, **kwargs):
        user = self.request.user
        customer = cart_service.get_customer(user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item, created = cart_service.add_variant(
                customer=customer,
                variant=serializer.validated_data["variant"],
                quantity=serializer.validated_data["quantity"],
            )
        except CartError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        output = self.get_serializer(item)
        return Response(output.data, status=201 if created else 200)

    def update(self, request, *args, **kwargs):
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        try:
            item = cart_service.update_quantity(
                item=item,
                customer=cart_service.get_customer(request.user),
                quantity=serializer.validated_data.get("quantity", item.quantity),
            )
        except CartError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(self.get_serializer(item).data)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if item.order.snapshot_at:
            raise ValidationError({"detail": "Cette commande est déjà figée."})
        return super().destroy(request, *args, **kwargs)
