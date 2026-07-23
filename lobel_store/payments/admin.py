import uuid

from django import forms
from django.contrib import admin, messages
from .models import (
    Payment, PaymentAuditEvent, PaymentOperationalAlert, PaymentWebhookEvent,
    Refund, RefundAttempt, RefundNotificationReceipt,
)
from .services.refund_service import RefundError, RefundService


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_select_related = ("order",)
    list_display = (
        "id", "order", "amount", "currency", "provider", "status", "created_at"
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
    list_display = (
        "id", "payment", "event_type", "signature_verified",
        "authentication_method", "created_at",
    )
    list_select_related = ("payment",)
    list_filter = ("event_type",)
    readonly_fields = [field.name for field in PaymentWebhookEvent._meta.fields]


@admin.register(PaymentAuditEvent)
class PaymentAuditEventAdmin(PaymentAdmin):
    list_display = ("id", "payment", "event_type", "from_status", "to_status", "created_at")
    list_select_related = ("payment",)
    list_filter = ("event_type", "to_status")
    readonly_fields = [field.name for field in PaymentAuditEvent._meta.fields]


@admin.register(PaymentOperationalAlert)
class PaymentOperationalAlertAdmin(PaymentAdmin):
    list_display = (
        "id", "severity", "alert_type", "payment", "order", "status", "created_at"
    )
    list_select_related = ("payment", "order")
    list_filter = ("status", "severity", "alert_type")
    search_fields = ("payment__id", "order__id", "message")
    readonly_fields = [
        field.name for field in PaymentOperationalAlert._meta.fields
    ]


class RefundRequestAdminForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ("payment", "amount", "reason", "idempotency_key")

    def clean_idempotency_key(self):
        return self.cleaned_data.get("idempotency_key") or uuid.uuid4().hex


@admin.action(description="Envoyer ou réessayer les remboursements sélectionnés")
def process_refunds(modeladmin, request, queryset):
    succeeded = failed = 0
    for refund in queryset:
        try:
            RefundService().process(refund_id=refund.id)
            succeeded += 1
        except RefundError as exc:
            failed += 1
            modeladmin.message_user(request, str(exc), level=messages.ERROR)
    modeladmin.message_user(
        request,
        f"{succeeded} remboursement(s) traité(s), {failed} échec(s).",
        level=messages.SUCCESS if not failed else messages.WARNING,
    )


@admin.action(description="Rapprocher les remboursements en cours")
def reconcile_refunds(modeladmin, request, queryset):
    succeeded = failed = 0
    for refund in queryset:
        try:
            RefundService().reconcile(refund_id=refund.id)
            succeeded += 1
        except RefundError as exc:
            failed += 1
            modeladmin.message_user(request, str(exc), level=messages.ERROR)
    modeladmin.message_user(
        request,
        f"{succeeded} rapprochement(s), {failed} échec(s).",
        level=messages.SUCCESS if not failed else messages.WARNING,
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    form = RefundRequestAdminForm
    list_display = (
        "id", "payment", "order", "amount", "currency", "status",
        "provider_reference", "requested_at",
    )
    list_select_related = ("payment", "order", "requested_by")
    list_filter = ("status", "currency", "affects_order_status")
    search_fields = (
        "id", "uuid", "payment__id", "order__id", "provider_reference"
    )
    actions = (process_refunds, reconcile_refunds)

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("payment", "amount", "reason", "idempotency_key")
        return tuple(field.name for field in Refund._meta.fields)

    def get_readonly_fields(self, request, obj=None):
        return () if obj is None else tuple(
            field.name for field in Refund._meta.fields
        )

    def save_model(self, request, obj, form, change):
        if change:
            return
        refund, _ = RefundService().request(
            payment=form.cleaned_data["payment"],
            amount=form.cleaned_data["amount"],
            reason=form.cleaned_data["reason"],
            actor=request.user,
            idempotency_key=form.cleaned_data["idempotency_key"],
        )
        obj.__dict__.update(refund.__dict__)

    def has_change_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RefundAttempt)
class RefundAttemptAdmin(PaymentAdmin):
    list_display = (
        "id", "refund", "sequence", "action", "result",
        "provider_status", "created_at",
    )
    list_select_related = ("refund",)
    list_filter = ("action", "result", "provider_status")
    readonly_fields = [field.name for field in RefundAttempt._meta.fields]


@admin.register(RefundNotificationReceipt)
class RefundNotificationReceiptAdmin(PaymentAdmin):
    list_display = (
        "id", "refund", "event_code", "status", "attempts", "sent_at"
    )
    list_select_related = ("refund",)
    list_filter = ("event_code", "status")
    readonly_fields = [
        field.name for field in RefundNotificationReceipt._meta.fields
    ]
