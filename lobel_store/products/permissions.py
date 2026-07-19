from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """Allow public catalogue reads and restrict every write to staff users."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_staff):
            return False
        if any(field in request.data for field in ("image", "video", "file")):
            return user.has_perm("products.add_productmedia")
        return True


class IsCatalogMediaManager(BasePermission):
    """Media writes require both staff status and the relevant Django permission."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated or not user.is_staff:
            return False
        action = getattr(view, "action", "")
        permission = "products.change_productmedia" if action in {"update", "partial_update", "archive"} else "products.add_productmedia"
        return user.has_perm(permission)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
