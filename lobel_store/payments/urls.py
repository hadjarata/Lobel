from rest_framework import routers
from django.urls import path

from .views import CheckoutView, MockPaymentConfirmView, PaymentViewSet, PaymentWebhookView

router = routers.DefaultRouter()
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='payment-checkout'),
    path('mock/confirm/', MockPaymentConfirmView.as_view(), name='payment-mock-confirm'),
    path('webhooks/ligdicash/', PaymentWebhookView.as_view(), name='payment-webhook'),
]

urlpatterns += router.urls
