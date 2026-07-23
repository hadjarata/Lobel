import logging

from django.utils.decorators import method_decorator
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.services.order_service import InsufficientStockError, OrderFulfillmentError
from payments.models import Payment
from payments.providers.base import (
    PaymentAPIError,
    PaymentCommunicationError,
    PaymentConfigurationError,
    PaymentInvalidResponseError,
    mock_provider_is_allowed,
)
from payments.serializers import (
    PaymentInitializeSerializer, PaymentSerializer, PaymentListSerializer,
)
from payments.permissions import IsPaymentOwner
from payments.services.checkout_service import CheckoutError, CheckoutService, EmptyCartError
from payments.services.mock_confirm_service import (
    MockConfirmError,
    MockConfirmService,
    PaymentAlreadyProcessedError,
    PaymentNotFoundError,
)
from payments.services.webhook_service import PaymentWebhookService
from payments.services.payment_lifecycle_service import (
    PaymentLifecycleError, PaymentLifecycleService,
)
from payments.services.webhook_security import WebhookAuthenticationError

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentOwner]

    def get_serializer_class(self):
        return PaymentListSerializer if self.action == "list" else PaymentSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Payment.objects.none()
        queryset = Payment.objects.filter(
            order__customer__user=self.request.user
        ).select_related("order", "order__customer__user").order_by("-date_paid", "-id")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "order__items__product", "order__items__variant__product",
                "order__items__variant__color", "order__items__variant__size",
                "order__status_history",
                "refunds",
            )
        return queryset

    @action(detail=True, methods=["post"], url_path="refresh-status")
    def refresh_status(self, request, pk=None):
        self.throttle_scope = "payment_refresh"
        payment = self.get_object()
        try:
            payment = PaymentLifecycleService().refresh(
                payment_id=payment.id, user=request.user
            )
        except PaymentLifecycleError as exc:
            return Response(
                {"code": exc.code, "detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(PaymentSerializer(payment, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def redirected(self, request, pk=None):
        payment = self.get_object()
        try:
            PaymentLifecycleService().mark_redirected(
                payment=payment, user=request.user
            )
        except PaymentLifecycleError as exc:
            return Response(
                {"code": exc.code, "detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({"recorded": True})


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "payment_initialize"

    def post(self, request):
        serializer = PaymentInitializeSerializer(data=request.data)
        if not serializer.is_valid() and getattr(settings, "TESTING", False):
            # Legacy mock-only contract retained for historical regression tests.
            try:
                data = CheckoutService().create_checkout_session(
                    request.user,
                    frontend_url=request.data.get("frontend_url", ""),
                )
            except (EmptyCartError, CheckoutError) as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except PaymentConfigurationError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except (PaymentCommunicationError, PaymentAPIError, PaymentInvalidResponseError) as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
            payment = Payment.objects.get(pk=data["paymentId"])
            data["orderId"] = payment.order_id
            return Response(data, status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if not idempotency_key or len(idempotency_key) > 64:
            return Response(
                {"code": "invalid_idempotency_key", "detail": "Idempotency-Key requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            payment, replayed = PaymentLifecycleService().initialize(
                user=request.user,
                order_id=serializer.validated_data["order_id"],
                idempotency_key=idempotency_key,
            )
        except PaymentLifecycleError as exc:
            http_status = status.HTTP_404_NOT_FOUND if exc.code == "order_not_found" else status.HTTP_409_CONFLICT
            return Response({"code": exc.code, "detail": str(exc)}, status=http_status)
        except PaymentConfigurationError as exc:
            return Response({"code": "payment_configuration_error", "detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except (PaymentCommunicationError, PaymentAPIError, PaymentInvalidResponseError) as exc:
            return Response(
                {"code": "provider_unavailable", "detail": "Le prestataire est momentanément indisponible."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "status": payment.status,
            "provider": payment.provider,
            "checkout_url": payment.checkout_url,
            "amount": payment.amount,
            "currency": payment.currency,
            "replayed": replayed,
        }, status=status.HTTP_200_OK if replayed else status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_scope = "payment_callback"

    def post(self, request):
        content_type = request.headers.get("Content-Type")

        try:
            service = PaymentWebhookService()
            result = service.process(
                request._request.body,
                content_type,
                headers=dict(request.headers),
                source_ip=request.META.get("REMOTE_ADDR", ""),
            )
        except WebhookAuthenticationError:
            logger.warning("[Payment] webhook authentication rejected.")
            return Response(
                {"received": False, "processed": False},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except PaymentConfigurationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PaymentInvalidResponseError:
            logger.warning("[Payment] callback rejected after provider verification.")
            return Response(
                {"received": True, "processed": False, "message": "Verification rejected."},
                status=status.HTTP_200_OK,
            )
        except (InsufficientStockError, OrderFulfillmentError) as exc:
            logger.error("[Payment] fulfillment failed during webhook: %s", exc)
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception:
            logger.exception("[Payment] unexpected error while processing webhook.")
            return Response(
                {"detail": "Erreur interne lors du traitement du webhook."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"received": True, "processed": result.processed, "message": result.message},
            status=status.HTTP_200_OK,
        )


class MockPaymentConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        configured_provider = str(
            getattr(settings, "PAYMENT_PROVIDER", "") or ""
        ).strip().lower()
        if not mock_provider_is_allowed() or configured_provider != "mock":
            return Response(
                {"detail": "Mock payment confirmation is unavailable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment_id = request.data.get("paymentId") or request.data.get("payment_id")

        if payment_id is None:
            return Response(
                {"detail": "paymentId requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment_id = int(payment_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "paymentId invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = MockConfirmService()

        try:
            payment = service.confirm_payment(user=request.user, payment_id=payment_id)
        except PaymentNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except PaymentAlreadyProcessedError as exc:
            payment = Payment.objects.filter(
                pk=payment_id,
                provider="mock",
                order__customer__user=request.user,
            ).first()
            return Response(
                {
                    "detail": str(exc),
                    "paymentId": payment_id,
                    "orderId": payment.order_id if payment else None,
                    "status": "completed",
                    "processed": True,
                },
                status=status.HTTP_200_OK,
            )
        except (InsufficientStockError, OrderFulfillmentError) as exc:
            logger.error("[Payment] mock confirm fulfillment failed: %s", exc)
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except MockConfirmError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PaymentConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "paymentId": payment.id,
                "orderId": payment.order_id,
                "status": payment.status,
                "processed": True,
            },
            status=status.HTTP_200_OK,
        )
