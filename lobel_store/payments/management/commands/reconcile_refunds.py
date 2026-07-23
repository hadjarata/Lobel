from django.core.management.base import BaseCommand, CommandError

from payments.models import Refund
from payments.services.refund_service import RefundError, RefundService


class Command(BaseCommand):
    help = "Rapproche les remboursements en cours auprès du prestataire."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--refund-id", type=int)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if not 1 <= options["limit"] <= 1000:
            raise CommandError("--limit doit être compris entre 1 et 1000.")
        queryset = Refund.objects.filter(
            status=Refund.STATUS_PROCESSING
        ).order_by("last_checked_at", "requested_at", "id")
        if options["refund_id"]:
            queryset = queryset.filter(pk=options["refund_id"])
        refunds = list(queryset[:options["limit"]])
        completed = failed = 0
        for refund in refunds:
            if options["dry_run"]:
                self.stdout.write(
                    f"DRY-RUN refund={refund.id} status={refund.status}"
                )
                continue
            try:
                updated = RefundService().reconcile(refund_id=refund.id)
                completed += int(updated.status == Refund.STATUS_COMPLETED)
                failed += int(updated.status == Refund.STATUS_FAILED)
                self.stdout.write(
                    f"refund={updated.id} status={updated.status}"
                )
            except RefundError as exc:
                failed += 1
                self.stderr.write(
                    f"refund={refund.id} code={exc.code} error={exc}"
                )
        self.stdout.write(
            f"examined={len(refunds)} completed={completed} "
            f"failed={failed} dry_run={options['dry_run']}"
        )
