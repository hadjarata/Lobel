from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from .admin import ProductMediaAdmin
from .models import ProductMedia


class MediaAdminTests(TestCase):
    def test_metadata_is_read_only_and_superuser_can_delete(self):
        model_admin = ProductMediaAdmin(ProductMedia, admin.site)
        request = RequestFactory().get("/admin/products/productmedia/")
        request.user = User.objects.create_superuser(
            username="admin-media",
            email="admin@example.com",
            password="password",
        )

        self.assertIn("checksum", model_admin.readonly_fields)
        self.assertTrue(model_admin.has_delete_permission(request))
