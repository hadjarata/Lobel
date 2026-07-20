from django.core.management.base import BaseCommand, CommandError

from orders.models import OrderNotificationReceipt
from orders.services.notification_service import OrderNotificationService


class Command(BaseCommand):
    help = "Relance les notifications de commande non envoyées."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--order-id", type=int)
        parser.add_argument("--event")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--failed-only", action="store_true")

    def handle(self, *args, **options):
        if options["limit"] <= 0:
            raise CommandError("--limit doit être positif.")
        queryset = OrderNotificationReceipt.objects.exclude(status="sent")
        if options["failed_only"]:
            queryset = queryset.filter(status="failed")
        if options["order_id"]:
            queryset = queryset.filter(order_id=options["order_id"])
        if options["event"]:
            queryset = queryset.filter(event_code=options["event"])
        receipts = queryset.order_by("created_at", "id")[:options["limit"]]
        examined = sent = 0
        for receipt in receipts:
            examined += 1
            if options["dry_run"]:
                self.stdout.write(
                    f"DRY-RUN receipt={receipt.id} order={receipt.order_id} "
                    f"event={receipt.event_code}"
                )
            else:
                sent += int(OrderNotificationService.dispatch(receipt.id))
        self.stdout.write(
            self.style.SUCCESS(
                f"examined={examined} sent={sent} dry_run={options['dry_run']}"
            )
        )
