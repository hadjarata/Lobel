import tempfile
from pathlib import PurePosixPath

from django.test import TestCase, override_settings

from .media_services import CatalogMediaService
from .models import Category, Product
from .tests_media_helpers import image_upload


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MediaStorageTests(TestCase):
    def test_physical_path_ignores_client_filename(self):
        product = Product.objects.create(
            name="Storage", category=Category.objects.create(name="Storage"), price=1
        )
        media = CatalogMediaService.add(
            product=product, media_type="image",
            upload=image_upload("../../C:\\temp\\evil.php.png"),
        )
        path = PurePosixPath(media.file.name)
        self.assertFalse(path.is_absolute())
        self.assertNotIn("..", path.parts)
        self.assertNotIn("evil", media.file.name)
        self.assertEqual(path.suffix, ".png")
