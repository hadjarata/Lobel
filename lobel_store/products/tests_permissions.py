from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Category, Collection, Product


class CataloguePermissionTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Shoes")
        self.product = Product.objects.create(
            name="Sneaker",
            category=self.category,
            price="25000.00",
        )
        self.collection = Collection.objects.create(
            name="Summer",
            image="collections/images/summer.jpg",
        )
        self.client_user = User.objects.create_user(
            username="client@example.com",
            password="password123",
        )
        self.admin_user = User.objects.create_user(
            username="admin@example.com",
            password="password123",
            is_staff=True,
        )

    def test_catalogue_reads_are_public(self):
        for url in (
            "/api/products/categories/",
            "/api/products/products/",
            "/api/products/collections/",
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_client_can_read_catalogue(self):
        self.client.force_authenticate(self.client_user)
        response = self.client.get(f"/api/products/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_writes_are_rejected(self):
        attempts = (
            ("/api/products/categories/", {"name": "Forbidden"}),
            (
                "/api/products/products/",
                {
                    "name": "Forbidden",
                    "category": self.category.id,
                    "price": "1000.00",
                },
            ),
            (
                "/api/products/collections/",
                {"name": "Forbidden", "cover_type": "image"},
            ),
        )
        for url, payload in attempts:
            with self.subTest(url=url):
                response = self.client.post(url, payload, format="json")
                self.assertIn(
                    response.status_code,
                    (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
                )

    def test_authenticated_client_cannot_create_catalogue_resources(self):
        self.client.force_authenticate(self.client_user)
        for url, payload in (
            ("/api/products/categories/", {"name": "Forbidden"}),
            (
                "/api/products/products/",
                {
                    "name": "Forbidden",
                    "category": self.category.id,
                    "price": "1000.00",
                },
            ),
            (
                "/api/products/collections/",
                {"name": "Forbidden", "cover_type": "image"},
            ),
        ):
            with self.subTest(url=url):
                response = self.client.post(url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_client_cannot_patch_or_delete_catalogue(self):
        self.client.force_authenticate(self.client_user)
        resources = (
            (
                f"/api/products/categories/{self.category.id}/",
                self.category,
                {"name": "Hacked"},
            ),
            (
                f"/api/products/products/{self.product.id}/",
                self.product,
                {"price": "1.00"},
            ),
            (
                f"/api/products/collections/{self.collection.slug}/",
                self.collection,
                {"is_active": False},
            ),
        )
        for url, instance, payload in resources:
            with self.subTest(url=url, method="patch"):
                response = self.client.patch(url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            with self.subTest(url=url, method="delete"):
                response = self.client.delete(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertTrue(type(instance).objects.filter(pk=instance.pk).exists())

    def test_staff_user_can_write_catalogue(self):
        self.client.force_authenticate(self.admin_user)

        category_response = self.client.post(
            "/api/products/categories/",
            {"name": "Accessories"},
            format="json",
        )
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)

        product_response = self.client.post(
            "/api/products/products/",
            {
                "name": "Bag",
                "category": category_response.data["id"],
                "price": "12000.00",
            },
            format="json",
        )
        self.assertEqual(product_response.status_code, status.HTTP_201_CREATED)

        collection_response = self.client.patch(
            f"/api/products/collections/{self.collection.slug}/",
            {"description": "Updated by staff"},
            format="json",
        )
        self.assertEqual(collection_response.status_code, status.HTTP_200_OK)
