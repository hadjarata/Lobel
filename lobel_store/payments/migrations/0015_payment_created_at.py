import django.utils.timezone
from django.db import migrations, models


def copy_creation_time(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    for payment in Payment.objects.only("id", "date_paid").iterator():
        Payment.objects.filter(pk=payment.pk).update(created_at=payment.date_paid)


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0014_paymentwebhookevent_authentication_method_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.RunPython(copy_creation_time, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="payment",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
