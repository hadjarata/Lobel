from django.core.management.base import BaseCommand

from products.media_validation import validate_image_upload, validate_video_upload
from products.models import Collection, ProductMedia


class Command(BaseCommand):
    help = "Audit referenced catalogue media without changing or deleting files."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", default=True)

    def handle(self, *args, **options):
        checked = invalid = missing = 0
        references = []
        for media in ProductMedia.objects.exclude(file=""):
            references.append((f"product-media:{media.pk}", media.media_type, media.file))
        for collection in Collection.objects.all():
            if collection.image:
                references.append((f"collection-image:{collection.pk}", "image", collection.image))
            if collection.video:
                references.append((f"collection-video:{collection.pk}", "video", collection.video))
        for label, media_type, field in references:
            if not field.storage.exists(field.name):
                missing += 1
                self.stdout.write(f"MISSING {label}")
                continue
            checked += 1
            original_name = field.name
            try:
                validator = validate_image_upload if media_type == "image" else validate_video_upload
                validator(field)
                self.stdout.write(f"OK {label}")
            except Exception as exc:
                invalid += 1
                self.stdout.write(f"INVALID {label} {exc.__class__.__name__}")
            finally:
                field.name = original_name
                field.seek(0)
        self.stdout.write(
            self.style.SUCCESS(
                f"dry-run complete: checked={checked} invalid={invalid} missing={missing}; nothing deleted"
            )
        )
