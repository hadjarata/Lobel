from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from payments.models import Payment
from payments.services.payment_lifecycle_service import PaymentLifecycleService


class Command(BaseCommand):
    help = "Revérifie de manière idempotente les paiements LigdiCash non terminaux."

    def add_arguments(self, parser):
        parser.add_argument("--age-minutes", type=int, default=15)
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--payment-id", type=int)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if options["age_minutes"] < 0 or not 1 <= options["limit"] <= 1000:
            raise CommandError("Options de réconciliation invalides.")
        query = Payment.objects.filter(
            provider="ligdicash",
            status__in=[
                "initializing", "pending", "redirect_required", "processing", "unknown",
            ],
            created_at__lte=timezone.now() - timedelta(minutes=options["age_minutes"]),
        ).order_by("created_at", "id")
        if options["payment_id"]:
            query = query.filter(id=options["payment_id"])
        payments = list(query[:options["limit"]])
        for payment in payments:
            if options["dry_run"]:
                self.stdout.write(f"DRY-RUN payment={payment.id} status={payment.status}")
                continue
            try:
                updated = PaymentLifecycleService().refresh(payment_id=payment.id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"payment={updated.id} status={updated.status}"
                    )
                )
            except Exception as exc:
                self.stderr.write(f"payment={payment.id} error={type(exc).__name__}")
        self.stdout.write(f"examined={len(payments)} dry_run={options['dry_run']}")
