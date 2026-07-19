import re

from orders.models import Order
from orders.services.lifecycle_service import (
    ALLOWED_ORDER_TRANSITIONS,
    OrderLifecycleService,
    OrderTransitionError,
)
from payments.models import Payment

ORDER_REFERENCE_PATTERN = re.compile(r"^LOBEL-ORDER-(\d+)$")


class OrderFulfillmentError(Exception):
    pass


class InsufficientStockError(OrderFulfillmentError):
    pass


class OrderService:
    def __init__(self, lifecycle_service=None):
        self.lifecycle_service = lifecycle_service or OrderLifecycleService()

    def fulfill_order(self, order: Order, payment: Payment | None = None) -> None:
        # Legacy test/import compatibility; all state changes are delegated to
        # the lifecycle boundary.
        if order.status == Order.STATUS_PAID:
            return
        try:
            self.lifecycle_service.transition_order(
                order=order,
                target_status=Order.STATUS_PAID,
                actor=None,
                payment=payment,
                reason_code="payment_verified",
                metadata={"payment_id": payment.id if payment else None},
            )
        except OrderTransitionError as exc:
            if exc.code == "insufficient_stock":
                raise InsufficientStockError(str(exc)) from exc
            raise OrderFulfillmentError(str(exc)) from exc

    @staticmethod
    def parse_order_id_from_reference(order_reference: str) -> int | None:
        match = ORDER_REFERENCE_PATTERN.match(order_reference)
        return int(match.group(1)) if match else None
