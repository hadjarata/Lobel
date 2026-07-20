from django.contrib import admin
from .models import (
    Order, OrderItem, OrderNotificationReceipt, OrderStatusHistory,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product", "variant", "quantity", "product_name", "variant_name",
        "unit_price", "currency", "subtotal",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = (
        "from_status", "to_status", "actor", "actor_role_snapshot",
        "reason_code", "reason_note", "metadata", "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'date_ordered', 'get_cart_total')
    list_select_related = ('customer__user',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items")
    list_filter = ('status', 'date_ordered')
    readonly_fields = (
        "status", "paid_at", "preparation_started_at", "shipped_at",
        "delivered_at", "cancelled_at", "refund_requested_at", "refunded_at",
        "stock_consumed_at", "stock_released_at",
    )
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'date_added')
    list_select_related = ('order', 'product', 'variant')
    readonly_fields = [field.name for field in OrderItem._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "from_status", "to_status", "actor", "created_at")
    list_select_related = ("order", "actor")
    readonly_fields = (
        "order", "from_status", "to_status", "actor", "actor_role_snapshot",
        "reason_code", "reason_note", "metadata", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


@admin.register(OrderNotificationReceipt)
class OrderNotificationReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order", "event_code", "channel", "status", "attempts", "sent_at",
    )
    list_filter = ("status", "event_code", "channel")
    readonly_fields = [field.name for field in OrderNotificationReceipt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
