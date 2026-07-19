from django.contrib import admin
from django.test import SimpleTestCase

from .admin import ProductMediaAdmin
from .models import ProductMedia


class MediaAdminTests(SimpleTestCase):
    def test_metadata_is_read_only_and_physical_delete_disabled(self):
        model_admin = ProductMediaAdmin(ProductMedia, admin.site)
        self.assertIn("checksum", model_admin.readonly_fields)
        self.assertFalse(model_admin.has_delete_permission(None))
