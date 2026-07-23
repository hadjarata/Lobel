import json
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.utils import timezone

from orders.models import Order
from payments.models import Payment, PaymentAuditEvent, PaymentOperationalAlert


class Command(BaseCommand):
    help = "Expose les métriques de santé paiement en JSON pour le monitoring."

    def add_arguments(self, parser):
        parser.add_argument("--window-minutes", type=int, default=60)
        parser.add_argument("--stale-minutes", type=int, default=30)
        parser.add_argument("--fail-on-alert", action="store_true")

    def handle(self, *args, **options):
        if options["window_minutes"] <= 0 or options["stale_minutes"] <= 0:
            raise CommandError("Les fenêtres doivent être positives.")
        now = timezone.now()
        since = now - timedelta(minutes=options["window_minutes"])
        stale_before = now - timedelta(minutes=options["stale_minutes"])
        recent = Payment.objects.filter(created_at__gte=since)
        initialized = recent.filter(initialized_at__isnull=False).count()
        init_failed = recent.filter(
            failure_code__in=["provider_communication_error", "provider_rejected"]
        ).count()
        confirmation_duration = ExpressionWrapper(
            F("confirmed_at") - F("created_at"), output_field=DurationField()
        )
        average = recent.filter(
            confirmed_at__isnull=False
        ).aggregate(value=Avg(confirmation_duration))["value"]
        metrics = {
            "window_minutes": options["window_minutes"],
            "initialization_total": initialized + init_failed,
            "initialization_failures": init_failed,
            "initialization_failure_rate": (
                round(init_failed / (initialized + init_failed), 4)
                if initialized + init_failed else 0
            ),
            "stale_unknown_or_processing": Payment.objects.filter(
                status__in=["unknown", "processing"],
                updated_at__lte=stale_before,
            ).count(),
            "webhooks_rejected": PaymentAuditEvent.objects.filter(
                event_type="webhook_rejected", created_at__gte=since
            ).count(),
            "duplicate_payments": PaymentAuditEvent.objects.filter(
                event_type="duplicate_payment_detected", created_at__gte=since
            ).count(),
            "refund_required_orders": Order.objects.filter(
                status=Order.STATUS_REFUND_REQUIRED
            ).count(),
            "amount_or_currency_mismatches": PaymentAuditEvent.objects.filter(
                event_type="webhook_rejected",
                created_at__gte=since,
                metadata__reason="PaymentInvalidResponseError",
            ).count(),
            "stock_errors_after_payment": PaymentAuditEvent.objects.filter(
                event_type="fulfillment_failed", created_at__gte=since
            ).count(),
            "open_critical_alerts": PaymentOperationalAlert.objects.filter(
                status="open", severity="critical"
            ).count(),
            "average_confirmation_seconds": (
                round(average.total_seconds(), 3) if average else None
            ),
        }
        self.stdout.write(json.dumps(metrics, sort_keys=True))
        alerting = (
            metrics["stale_unknown_or_processing"]
            or metrics["webhooks_rejected"]
            or metrics["duplicate_payments"]
            or metrics["refund_required_orders"]
            or metrics["amount_or_currency_mismatches"]
            or metrics["stock_errors_after_payment"]
            or metrics["open_critical_alerts"]
        )
        if options["fail_on_alert"] and alerting:
            raise CommandError("Des anomalies de paiement nécessitent une intervention.")
