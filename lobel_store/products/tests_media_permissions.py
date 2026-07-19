import tempfile

from django.contrib.auth.models import Permission, User
from django.test import override_settings
from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import Category, Product, ProductMedia
from .tests_media_helpers import image_upload


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MediaPermissionTests(APITestCase):
    def setUp(self):
        cache.clear()
        category = Category.objects.create(name="Media")
        self.product = Product.objects.create(name="Article", category=category, price=100)
        self.client_user = User.objects.create_user("client-media")
        self.staff = User.objects.create_user("staff-media", is_staff=True)
        self.manager = User.objects.create_user("manager-media", is_staff=True)
        self.manager.user_permissions.add(Permission.objects.get(codename="add_productmedia"))

    def tearDown(self):
        cache.clear()

    def post(self):
        return self.client.post("/api/products/media/", {
            "product": self.product.pk, "media_type": "image", "file": image_upload(),
        }, format="multipart")

    def test_anonymous_and_client_cannot_upload(self):
        self.assertIn(self.post().status_code, (401, 403))
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.post().status_code, 403)
        self.assertEqual(ProductMedia.objects.count(), 0)

    def test_staff_without_explicit_permission_cannot_upload(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.post().status_code, 403)

    def test_authorized_manager_can_upload_and_public_can_read(self):
        self.client.force_authenticate(self.manager)
        response = self.post()
        self.assertEqual(response.status_code, 201, response.data)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/products/media/").status_code, 200)

    @override_settings(MAX_PRODUCT_IMAGES=100)
    def test_upload_scope_is_throttled(self):
        self.client.force_authenticate(self.manager)
        responses = [self.post() for _ in range(31)]
        self.assertEqual(responses[-1].status_code, 429)
