from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0008_collection_checksum_collection_duration_seconds_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productvariant",
            name="color",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="products.color",
            ),
        ),
        migrations.AlterField(
            model_name="productvariant",
            name="size",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="products.size",
            ),
        ),
    ]
