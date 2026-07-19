from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Lower, Trim
from django.utils import timezone


def prepare_existing_accounts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Customer = apps.get_model("users", "Customer")
    duplicates = list(
        User.objects.annotate(normalized=Lower(Trim("email")))
        .exclude(normalized="")
        .values("normalized")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .values_list("normalized", flat=True)
    )
    if duplicates:
        raise RuntimeError(
            "Case-insensitive duplicate user e-mails must be resolved manually "
            "before applying users.0004; no accounts were merged or deleted."
        )
    Customer.objects.filter(
        user__is_active=True, email_verified_at__isnull=True
    ).update(email_verified_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [("users", "0003_customer_email_verified_at_customer_suspended_at_and_more")]

    operations = [
        migrations.RunPython(prepare_existing_accounts, migrations.RunPython.noop),
        migrations.RunSQL(
            sql=(
                "CREATE UNIQUE INDEX unique_auth_user_email_ci "
                "ON auth_user (LOWER(BTRIM(email))) WHERE BTRIM(email) <> '';"
            ),
            reverse_sql="DROP INDEX IF EXISTS unique_auth_user_email_ci;",
        ),
    ]
