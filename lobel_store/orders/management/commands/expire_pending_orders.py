from django.core.management.base import BaseCommand, CommandError

from orders.services.expiration_service import OrderExpirationService
from orders.services.lifecycle_service import OrderTransitionError


class Command(BaseCommand):
    help = "Expire les commandes impayées arrivées à échéance."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--older-than", type=int)
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--order-id", type=int)

    def handle(self, *args, **options):
        if options["limit"] <= 0:
            raise CommandError("--limit doit être positif.")
        if options["older_than"] is not None and options["older_than"] <= 0:
            raise CommandError("--older-than doit être positif.")
        service = OrderExpirationService()
        candidates = service.candidates(
            older_than=options["older_than"], order_id=options["order_id"]
        )[:options["limit"]]
        examined = expired = failed = 0
        for order in candidates:
            examined += 1
            if options["dry_run"]:
                self.stdout.write(f"DRY-RUN order={order.id} status={order.status}")
                continue
            try:
                _, changed = service.expire(order)
                expired += int(changed)
            except OrderTransitionError as exc:
                failed += 1
                self.stderr.write(f"order={order.id} error={exc}")
        self.stdout.write(
            self.style.SUCCESS(
                f"examined={examined} expired={expired} failed={failed} "
                f"dry_run={options['dry_run']}"
            )
        )
