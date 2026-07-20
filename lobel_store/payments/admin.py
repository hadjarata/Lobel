from django.contrib import admin
from .models import Payment, PaymentAuditEvent, PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_select_related = ("order",)
    list_display = (
        "id", "order", "amount", "currency", "provider", "status", "date_paid"
    )
    list_filter = ("provider", "status", "currency")
    readonly_fields = [field.name for field in Payment._meta.fields]

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


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(PaymentAdmin):
    list_display = ("id", "payment", "event_type", "created_at")
    list_select_related = ("payment",)
    list_filter = ("event_type",)
    readonly_fields = [field.name for field in PaymentWebhookEvent._meta.fields]


@admin.register(PaymentAuditEvent)
class PaymentAuditEventAdmin(PaymentAdmin):
    list_display = ("id", "payment", "event_type", "from_status", "to_status", "created_at")
    list_select_related = ("payment",)
    list_filter = ("event_type", "to_status")
    readonly_fields = [field.name for field in PaymentAuditEvent._meta.fields]
