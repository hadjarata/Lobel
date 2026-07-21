import content.models
from django.db import migrations, models


def preserve_single_home_hero(apps, schema_editor):
    HomeHero = apps.get_model("content", "HomeHero")
    selected = HomeHero.objects.order_by(
        "-is_active", "-updated_at", "-id"
    ).first()
    if selected is None:
        return

    if selected.media_type == "VIDEO" and selected.video:
        selected.desktop_image = ""
    elif selected.desktop_image:
        selected.media_type = "IMAGE"
        selected.video = ""
    elif selected.video:
        selected.media_type = "VIDEO"
        selected.desktop_image = ""
    else:
        selected.media_type = "IMAGE"
        selected.desktop_image = ""
        selected.video = ""

    selected.save(update_fields=("media_type", "desktop_image", "video"))
    HomeHero.objects.exclude(pk=selected.pk).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0002_customdressservice"),
    ]

    operations = [
        migrations.RunPython(
            preserve_single_home_hero,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="homehero",
            name="unique_active_home_hero",
        ),
        migrations.RenameField(
            model_name="homehero",
            old_name="desktop_image",
            new_name="image",
        ),
        migrations.RemoveField(model_name="homehero", name="created_at"),
        migrations.RemoveField(model_name="homehero", name="eyebrow"),
        migrations.RemoveField(model_name="homehero", name="is_active"),
        migrations.RemoveField(model_name="homehero", name="mobile_image"),
        migrations.RemoveField(model_name="homehero", name="primary_button_label"),
        migrations.RemoveField(model_name="homehero", name="primary_button_url"),
        migrations.RemoveField(model_name="homehero", name="publish_at"),
        migrations.RemoveField(model_name="homehero", name="secondary_button_label"),
        migrations.RemoveField(model_name="homehero", name="secondary_button_url"),
        migrations.RemoveField(model_name="homehero", name="updated_at"),
        migrations.RemoveField(model_name="homehero", name="video_poster"),
        migrations.AlterField(
            model_name="homehero",
            name="description",
            field=models.TextField(
                default=(
                    "Découvrez notre sélection de créations et explorez notre boutique."
                ),
                max_length=600,
                verbose_name="description",
            ),
        ),
        migrations.AlterField(
            model_name="homehero",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text=(
                    "JPEG, PNG ou WebP. Obligatoire pour une couverture image."
                ),
                null=True,
                upload_to=content.models.hero_upload_to,
                verbose_name="image",
            ),
        ),
        migrations.AlterField(
            model_name="homehero",
            name="media_type",
            field=models.CharField(
                choices=[("IMAGE", "Image"), ("VIDEO", "Vidéo")],
                default="IMAGE",
                max_length=10,
                verbose_name="type de couverture",
            ),
        ),
        migrations.AlterField(
            model_name="homehero",
            name="title",
            field=models.CharField(
                default="Bienvenue sur LobelStore",
                max_length=180,
                verbose_name="titre",
            ),
        ),
        migrations.AlterField(
            model_name="homehero",
            name="video",
            field=models.FileField(
                blank=True,
                help_text="MP4 H.264. Obligatoire pour une couverture vidéo.",
                null=True,
                upload_to=content.models.hero_upload_to,
                verbose_name="vidéo",
            ),
        ),
        migrations.AlterModelOptions(
            name="homehero",
            options={
                "verbose_name": "couverture de l'accueil",
                "verbose_name_plural": "couverture de l'accueil",
            },
        ),
        migrations.AddConstraint(
            model_name="homehero",
            constraint=models.UniqueConstraint(
                models.Value(1),
                name="single_home_hero_configuration",
            ),
        ),
    ]
