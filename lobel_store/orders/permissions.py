from rest_framework.permissions import BasePermission


class IsOrderOwner(BasePermission):
    """Restrict order objects to the customer linked to the request user."""

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or (obj.customer_id and obj.customer.user_id == request.user.id)
            )
        )
