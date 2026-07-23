from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from orders.models import Order
from orders.services.lifecycle_service import OrderLifecycleService, OrderTransitionError


class OrderExpirationService:
    PAYABLE_STATUSES = {
        Order.STATUS_PENDING_PAYMENT,
        Order.STATUS_PAYMENT_PROCESSING,
        Order.STATUS_PAYMENT_FAILED,
    }

    def candidates(self, *, older_than=None, order_id=None):
        minutes = older_than or settings.ORDER_PENDING_PAYMENT_TTL_MINUTES
        now = timezone.now()
        cutoff = now - timedelta(minutes=minutes)
        expiration_filter = (
            Q(date_ordered__lt=cutoff)
            if older_than is not None
            else (
                Q(stock_reservation_expires_at__lte=now)
                | Q(
                    stock_reservation_expires_at__isnull=True,
                    date_ordered__lt=cutoff,
                )
            )
        )
        queryset = Order.objects.filter(
            status__in=self.PAYABLE_STATUSES,
            paid_at__isnull=True,
            stock_consumed_at__isnull=True,
        ).filter(expiration_filter).exclude(
            payments__status="completed"
        ).distinct().order_by("date_ordered", "id")
        if order_id is not None:
            queryset = queryset.filter(pk=order_id)
        return queryset

    @transaction.atomic
    def expire(self, order):
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status == Order.STATUS_EXPIRED:
            return order, False
        if order.status not in self.PAYABLE_STATUSES:
            raise OrderTransitionError("Commande non éligible à l'expiration.")
        completed = order.payments.select_for_update().filter(status="completed").first()
        if completed:
            raise OrderTransitionError("Une commande payée ne peut pas expirer.")
        return OrderLifecycleService().transition_order(
            order=order,
            target_status=Order.STATUS_EXPIRED,
            actor=None,
            reason_code="payment_expired",
            source="expiration",
        )
