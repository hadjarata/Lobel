from rest_framework.permissions import BasePermission


class IsPaymentOwner(BasePermission):
    """Restrict payment objects to the customer linked to the request user."""

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.order.customer_id
            and obj.order.customer.user_id == request.user.id
        )
