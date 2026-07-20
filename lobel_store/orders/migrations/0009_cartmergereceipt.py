import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0008_alter_orderitem_order"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CartMergeReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("idempotency_key", models.CharField(max_length=64)),
                ("request_fingerprint", models.CharField(max_length=64)),
                ("response_payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cart_merge_receipts", to="users.customer")),
            ],
            options={"constraints": [
                models.UniqueConstraint(fields=("customer", "idempotency_key"), name="unique_cart_merge_key_per_customer"),
            ]},
        ),
    ]
