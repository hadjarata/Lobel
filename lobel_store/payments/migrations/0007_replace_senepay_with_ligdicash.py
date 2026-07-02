from django.db import migrations, models


def migrate_senepay_to_ligdicash(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    Payment.objects.filter(provider="senepay").update(provider="ligdicash")
    Payment.objects.filter(payment_method="senepay").update(payment_method="ligdicash")


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_paymentwebhookevent'),
    ]

    operations = [
        migrations.RunPython(migrate_senepay_to_ligdicash, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(choices=[('card', 'Card'), ('paypal', 'PayPal'), ('cash', 'Cash'), ('ligdicash', 'LigdiCash')], max_length=20),
        ),
        migrations.AlterField(
            model_name='payment',
            name='provider',
            field=models.CharField(choices=[('manual', 'Manual'), ('ligdicash', 'LigdiCash')], default='manual', max_length=30),
        ),
    ]
