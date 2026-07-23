import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0013_order_stock_reservation"),
        ("payments", "0010_payment_lifecycle"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="status",
            field=models.CharField(
                choices=[
                    ("created", "Created"),
                    ("initializing", "Initializing"),
                    ("pending", "Pending"),
                    ("redirect_required", "Redirect required"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                    ("cancelled", "Cancelled"),
                    ("expired", "Expired"),
                    ("refund_required", "Refund required"),
                    ("unknown", "Unknown"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="PaymentOperationalAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alert_type", models.CharField(max_length=50)),
                ("severity", models.CharField(choices=[("warning", "Warning"), ("critical", "Critical")], default="critical", max_length=20)),
                ("status", models.CharField(choices=[("open", "Open"), ("resolved", "Resolved")], default="open", max_length=20)),
                ("message", models.CharField(max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_alerts", to="orders.order")),
                ("payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_alerts", to="payments.payment")),
            ],
            options={
                "ordering": ["-created_at", "-id"],
                "indexes": [models.Index(fields=["status", "severity", "created_at"], name="payment_alert_queue_idx")],
                "constraints": [models.UniqueConstraint(fields=("payment", "alert_type"), name="unique_payment_operational_alert")],
            },
        ),
    ]
