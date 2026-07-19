import logging

from django.utils.decorators import method_decorator
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status, viewsets
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
from payments.serializers import PaymentSerializer
from payments.permissions import IsPaymentOwner
from payments.services.checkout_service import CheckoutService, EmptyCartError
from payments.services.mock_confirm_service import (
    MockConfirmError,
    MockConfirmService,
    PaymentAlreadyProcessedError,
    PaymentNotFoundError,
)
from payments.services.webhook_service import PaymentWebhookService

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentOwner]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Payment.objects.none()
        return Payment.objects.filter(order__customer__user=self.request.user)


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        frontend_url = (
            request.data.get('frontend_url')
            or request.data.get('frontendUrl')
            or request.headers.get('Origin')
            or ''
        )

        try:
            service = CheckoutService()
            checkout_data = service.create_checkout_session(
                request.user,
                frontend_url=frontend_url,
            )
        except EmptyCartError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PaymentConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (PaymentCommunicationError, PaymentAPIError, PaymentInvalidResponseError) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment = Payment.objects.only("order_id").get(pk=checkout_data["paymentId"])
        checkout_data["orderId"] = payment.order_id

        return Response(checkout_data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        content_type = request.headers.get("Content-Type")

        try:
            service = PaymentWebhookService()
            result = service.process(request._request.body, content_type)
        except PaymentConfigurationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
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
