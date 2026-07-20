from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("orders", "0009_cartmergereceipt")]

    operations = [
        migrations.AddField(model_name="order", name="billing_address", field=models.TextField(blank=True)),
        migrations.AddField(model_name="order", name="billing_same_as_shipping", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="order", name="checkout_version", field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name="order", name="delivery_city", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="order", name="delivery_district", field=models.CharField(blank=True, max_length=150)),
        migrations.AddField(model_name="order", name="delivery_eta_max_days", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="order", name="delivery_eta_min_days", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="order", name="delivery_instructions", field=models.CharField(blank=True, max_length=500)),
        migrations.AddField(model_name="order", name="delivery_method_code", field=models.CharField(blank=True, max_length=50)),
        migrations.AddField(model_name="order", name="delivery_method_label", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="order", name="delivery_region", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="order", name="delivery_street", field=models.CharField(blank=True, max_length=250)),
        migrations.CreateModel(
            name="CheckoutCreationReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("idempotency_key", models.CharField(max_length=64)),
                ("request_fingerprint", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="checkout_creation_receipts", to="users.customer")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="checkout_creation_receipts", to="orders.order")),
            ],
        ),
        migrations.AddConstraint(
            model_name="checkoutcreationreceipt",
            constraint=models.UniqueConstraint(fields=("customer", "idempotency_key"), name="unique_checkout_key_per_customer"),
        ),
    ]
