from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_collection_video_product_collections_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='cover_type',
            field=models.CharField(
                choices=[('image', 'Image'), ('video', 'Video')],
                default='image',
                max_length=10,
            ),
        ),
    ]
