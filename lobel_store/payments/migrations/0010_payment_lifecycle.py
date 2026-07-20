import uuid
from django.db import migrations, models
import django.db.models.deletion


def populate_payment_uuids(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    for payment in Payment.objects.filter(uuid__isnull=True).iterator():
        payment.uuid = uuid.uuid4()
        payment.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    dependencies = [("payments", "0009_alter_payment_order")]
    operations = [
        migrations.AddField(model_name="payment", name="uuid", field=models.UUIDField(blank=True, editable=False, null=True)),
        migrations.RunPython(populate_payment_uuids, migrations.RunPython.noop),
        migrations.AlterField(model_name="payment", name="uuid", field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        migrations.AddField(model_name="payment", name="merchant_reference", field=models.CharField(blank=True, max_length=64, null=True, unique=True)),
        migrations.AddField(model_name="payment", name="idempotency_key", field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name="payment", name="request_fingerprint", field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name="payment", name="provider_status", field=models.CharField(blank=True, max_length=50)),
        migrations.AddField(model_name="payment", name="checkout_url", field=models.URLField(blank=True, max_length=1000)),
        migrations.AddField(model_name="payment", name="initialized_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="redirected_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="confirmed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="failed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="cancelled_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="expired_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="last_checked_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="failure_code", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="payment", name="failure_message", field=models.CharField(blank=True, max_length=500)),
        migrations.AddField(model_name="payment", name="provider_payload", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="payment", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.AlterField(model_name="payment", name="status", field=models.CharField(choices=[("created", "Created"), ("initializing", "Initializing"), ("pending", "Pending"), ("redirect_required", "Redirect required"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("expired", "Expired"), ("unknown", "Unknown")], default="pending", max_length=20)),
        migrations.AddConstraint(model_name="payment", constraint=models.UniqueConstraint(condition=~models.Q(idempotency_key=""), fields=("order", "idempotency_key"), name="unique_payment_key_per_order")),
        migrations.CreateModel(
            name="PaymentAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=50)),
                ("from_status", models.CharField(blank=True, max_length=20)),
                ("to_status", models.CharField(blank=True, max_length=20)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="payments.payment")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
    ]
