from html import escape

from django.db.models import Prefetch, Q
from django.http import HttpResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem
from .serializers import (
    CartMergeSerializer, CheckoutRequestSerializer, DeliveryOptionsRequestSerializer,
    OrderSerializer, OrderItemSerializer, OrderListSerializer,
    OrderCancellationSerializer,
)
from .services.cart_service import CartError, CartService
from .services.lifecycle_service import OrderLifecycleService, OrderTransitionError
from .services.order_checkout_service import OrderCheckoutError, OrderCheckoutService
from .permissions import IsOrderOwner

cart_service = CartService()
lifecycle_service = OrderLifecycleService()
order_checkout_service = OrderCheckoutService()

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
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(id__icontains=search))
        ordering = self.request.query_params.get("ordering", "-date_ordered")
        if ordering not in {"date_ordered", "-date_ordered", "id", "-id"}:
            ordering = "-date_ordered"

        complete_param = self.request.query_params.get("complete")
        if complete_param is not None:
            if complete_param.lower() in ("true", "1"):
                queryset = queryset.filter(complete=True)
            elif complete_param.lower() in ("false", "0"):
                queryset = queryset.filter(complete=False)

        queryset = queryset.select_related("customer__user").order_by(ordering, "-id")
        items = OrderItem.objects.select_related(
            "product", "variant__product", "variant__color", "variant__size"
        ).order_by("id")
        if self.action == "list":
            return queryset.prefetch_related(
                Prefetch("items", queryset=items), "payments"
            )
        return queryset.prefetch_related(
            Prefetch("items", queryset=items), "status_history", "payments"
        )

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

    @action(detail=False, methods=["post"], url_path="cart/merge")
    def merge_cart(self, request):
        serializer = CartMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if not idempotency_key or len(idempotency_key) > 64:
            return Response(
                {"code": "invalid_idempotency_key", "detail": "Idempotency-Key requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        customer = cart_service.get_customer(request.user)
        try:
            report, replayed = cart_service.merge_guest_items(
                customer=customer,
                items=serializer.validated_data["items"],
                idempotency_key=idempotency_key,
            )
        except CartError as exc:
            return Response(
                {"code": exc.code, "detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        cart = cart_service.get_active_cart(customer, prefetch=True, create=False)
        return Response({
            **report,
            "cart": (
                OrderSerializer(cart, context={"request": request}).data
                if cart else cart_service.empty_cart_payload()
            ),
            "replayed": replayed,
        })

    @action(detail=False, methods=["delete"], url_path="cart/clear")
    def clear_cart(self, request):
        customer = cart_service.get_customer(request.user)
        try:
            cart_service.clear_cart(customer)
        except CartError as exc:
            return Response(
                {"code": exc.code, "detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(cart_service.empty_cart_payload())

    def _checkout_error(self, exc):
        return Response(
            {"code": exc.code, "detail": str(exc), **({"errors": exc.errors} if exc.errors else {})},
            status=(
                status.HTTP_400_BAD_REQUEST
                if exc.code in {"checkout_invalid", "customer_missing", "invalid_delivery_method"}
                else status.HTTP_409_CONFLICT
            ),
        )

    @action(detail=False, methods=["post"], url_path="checkout/delivery-options")
    def checkout_delivery_options(self, request):
        serializer = DeliveryOptionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            "delivery_methods": order_checkout_service.delivery_options(
                serializer.validated_data["shipping_address"]
            )
        })

    @action(detail=False, methods=["post"], url_path="checkout/preview")
    def checkout_preview(self, request):
        serializer = CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(order_checkout_service.preview(request.user, serializer.validated_data))
        except OrderCheckoutError as exc:
            return self._checkout_error(exc)

    @action(detail=False, methods=["post"], url_path="checkout/create-order")
    def checkout_create_order(self, request):
        serializer = CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data.get("checkout_version"):
            return Response(
                {"code": "checkout_version_required", "detail": "checkout_version requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if not idempotency_key or len(idempotency_key) > 64:
            return Response(
                {"code": "invalid_idempotency_key", "detail": "Idempotency-Key requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            order, replayed = order_checkout_service.create_order(
                request.user, serializer.validated_data, idempotency_key
            )
        except OrderCheckoutError as exc:
            return self._checkout_error(exc)
        order.refresh_from_db()
        return Response(
            {
                "order": OrderSerializer(order, context={"request": request}).data,
                "replayed": replayed,
                "next_action": "payment_initialization",
            },
            status=status.HTTP_200_OK if replayed else status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="checkout/pending")
    def checkout_pending(self, request):
        order = order_checkout_service.pending_order(request.user)
        if order is None:
            return Response({"order": None})
        return Response({"order": OrderSerializer(order, context={"request": request}).data})

    def _transition(
        self, request, target_status, *, require_reason=False,
        reason_code=None, reason_note=None,
    ):
        order = self.get_object()
        reason_code = (
            str(request.data.get("reason_code", "")).strip()
            if reason_code is None else reason_code
        )
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
                reason_note=(
                    request.data.get("reason_note", "")
                    if reason_note is None else reason_note
                ),
                source="customer_api" if not request.user.is_staff else "staff_api",
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
        serializer = OrderCancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._transition(
            request, Order.STATUS_CANCELLED, require_reason=True,
            reason_code="customer_request",
            reason_note=serializer.validated_data.get("reason", ""),
        )

    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        order = self.get_object()
        if not order.paid_at:
            return Response(
                {"code": "receipt_unavailable", "detail": "Reçu indisponible."},
                status=status.HTTP_409_CONFLICT,
            )
        payment = order.payments.filter(status="completed").order_by("-id").first()
        rows = "".join(
            "<tr>"
            f"<td>{escape(item.product_name or 'Produit')}</td>"
            f"<td>{escape(item.variant_name or '')}</td>"
            f"<td>{item.quantity}</td>"
            f"<td>{escape(str(item.unit_price))}</td>"
            f"<td>{escape(str(item.subtotal))}</td>"
            "</tr>"
            for item in order.items.all()
        )
        reference = (
            payment.merchant_reference or payment.order_reference
            if payment else order.transaction_id or ""
        )
        document = (
            "<!doctype html><html lang=\"fr\"><meta charset=\"utf-8\">"
            f"<title>Reçu commande {order.id}</title><body><h1>LobelStore</h1>"
            "<h2>Justificatif de commande</h2>"
            f"<p>Commande #{order.id}</p><p>Date : {order.paid_at:%Y-%m-%d %H:%M}</p>"
            f"<p>Référence paiement : {escape(reference)}</p>"
            "<table><thead><tr><th>Article</th><th>Variante</th><th>Qté</th>"
            f"<th>Prix</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table>"
            f"<p>Sous-total : {order.subtotal_amount} {order.currency}</p>"
            f"<p>Livraison : {order.shipping_amount} {order.currency}</p>"
            f"<p>Réduction : {order.discount_amount} {order.currency}</p>"
            f"<strong>Total : {order.total_amount} {order.currency}</strong>"
            "<p>Ce document est un justificatif de commande, pas une facture fiscale.</p>"
            "</body></html>"
        )
        response = HttpResponse(document, content_type="text/html; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="lobelstore-recu-commande-{order.id}.html"'
        )
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["X-Content-Type-Options"] = "nosniff"
        return response

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
            raise ValidationError({
                "code": exc.code,
                "detail": str(exc),
                **({"available_quantity": exc.available_quantity}
                   if exc.available_quantity is not None else {}),
            }) from exc
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
            raise ValidationError({
                "code": exc.code,
                "detail": str(exc),
                **({"available_quantity": exc.available_quantity}
                   if exc.available_quantity is not None else {}),
            }) from exc
        return Response(self.get_serializer(item).data)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if item.order.snapshot_at:
            raise ValidationError({"detail": "Cette commande est déjà figée."})
        return super().destroy(request, *args, **kwargs)
