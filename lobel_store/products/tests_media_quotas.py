import tempfile
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from rest_framework.exceptions import ValidationError

from .media_services import CatalogMediaService
from .models import Category, Product, ProductMedia
from .tests_media_helpers import image_upload


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), MAX_PRODUCT_IMAGES=1)
class MediaQuotaTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.product = Product.objects.create(
            name="Quota", category=Category.objects.create(name="Quota"), price=1
        )

    def add(self, index):
        close_old_connections()
        try:
            CatalogMediaService.add(
                product=self.product, media_type="image",
                upload=image_upload(f"{index}.png"),
            )
            return "created"
        except ValidationError:
            return "quota"
        finally:
            close_old_connections()

    def test_concurrent_uploads_do_not_exceed_quota(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(self.add, range(2)))
        self.assertCountEqual(results, ["created", "quota"])
        self.assertEqual(ProductMedia.objects.filter(is_active=True).count(), 1)
