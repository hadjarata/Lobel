from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0012_orderreceipt"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="stock_reserved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="stock_reservation_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
