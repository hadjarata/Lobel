import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from content.models import (
    CustomDressService,
    HomeHero,
    validate_whatsapp_phone,
)
from content.admin import (
    CustomDressServiceAdminForm,
    HomeHeroAdmin,
    HomeHeroAdminForm,
)
from products.tests_media_helpers import image_upload


TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA,
    HOME_HERO_MAX_IMAGE_SIZE_BYTES=1024 * 1024,
    HOME_HERO_MAX_VIDEO_SIZE_BYTES=1024 * 1024,
)
class HomeHeroTests(TestCase):
    def image_hero(self, **overrides):
        data = {
            "media_type": HomeHero.MEDIA_IMAGE,
            "image": image_upload(),
        }
        data.update(overrides)
        return HomeHero(**data)

    def video_hero(self, **overrides):
        data = {
            "media_type": HomeHero.MEDIA_VIDEO,
            "video": SimpleUploadedFile(
                "hero.mp4", b"small-mp4", content_type="video/mp4"
            ),
        }
        data.update(overrides)
        return HomeHero(**data)

    def save_valid_video(self, hero):
        with patch(
            "content.models.validate_video_upload",
            return_value={"format": "MP4"},
        ):
            hero.full_clean()
            hero.save()
        return hero

    def test_default_title_and_description(self):
        hero = HomeHero()
        self.assertEqual(hero.title, "Bienvenue sur LobelStore")
        self.assertEqual(
            hero.description,
            "Découvrez notre sélection de créations et explorez notre boutique.",
        )

    def test_valid_image(self):
        hero = self.image_hero()
        hero.full_clean()
        hero.save()
        self.assertIsNotNone(hero.pk)

    def test_valid_video(self):
        self.assertIsNotNone(self.save_valid_video(self.video_hero()).pk)

    def test_image_required(self):
        with self.assertRaises(ValidationError):
            self.image_hero(image=None).full_clean()

    def test_video_required(self):
        with self.assertRaises(ValidationError):
            self.video_hero(video=None).full_clean()

    def test_image_and_video_are_mutually_exclusive(self):
        with self.assertRaises(ValidationError):
            self.image_hero(video=self.video_hero().video).full_clean()
        with self.assertRaises(ValidationError):
            self.video_hero(image=image_upload()).full_clean()

    def test_forbidden_image_type(self):
        hero = self.image_hero(
            image=SimpleUploadedFile(
                "hero.svg", b"<svg/>", content_type="image/svg+xml"
            )
        )
        with self.assertRaises(ValidationError):
            hero.full_clean()

    def test_forbidden_video_type(self):
        hero = self.video_hero(
            video=SimpleUploadedFile("hero.avi", b"avi", content_type="video/avi")
        )
        with self.assertRaises(ValidationError):
            hero.full_clean()

    @override_settings(HOME_HERO_MAX_IMAGE_SIZE_BYTES=4)
    def test_image_too_large(self):
        with self.assertRaises(ValidationError):
            self.image_hero().full_clean()

    @override_settings(HOME_HERO_MAX_VIDEO_SIZE_BYTES=4)
    def test_video_too_large(self):
        with self.assertRaises(ValidationError):
            self.video_hero().full_clean()

    def test_single_configuration_constraint(self):
        first = self.image_hero(title="Première")
        first.full_clean()
        first.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.image_hero(title="Seconde").save()

    def test_public_endpoint_image_contract(self):
        hero = self.image_hero(title="Bienvenue")
        hero.full_clean()
        hero.save()
        data = self.client.get("/api/content/home-hero/").json()
        self.assertEqual(
            set(data), {"title", "description", "media_type", "media_url"}
        )
        self.assertEqual(data["title"], "Bienvenue")
        self.assertEqual(data["media_type"], HomeHero.MEDIA_IMAGE)
        self.assertTrue(data["media_url"].startswith("http://testserver/media/"))

    def test_public_endpoint_video_contract(self):
        hero = self.save_valid_video(self.video_hero())
        data = self.client.get("/api/content/home-hero/").json()
        self.assertEqual(data["media_type"], HomeHero.MEDIA_VIDEO)
        self.assertTrue(data["media_url"].endswith(".mp4"))

    def test_no_configuration_returns_204(self):
        response = self.client.get("/api/content/home-hero/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Cache-Control"], "public, max-age=60")

    def test_old_and_internal_fields_are_not_exposed(self):
        hero = self.image_hero()
        hero.full_clean()
        hero.save()
        data = self.client.get("/api/content/home-hero/").json()
        for field in (
            "id", "eyebrow", "desktop_image_url", "mobile_image_url",
            "video_url", "video_poster_url", "primary_button", "secondary_button",
            "is_active", "publish_at", "created_at", "updated_at",
        ):
            self.assertNotIn(field, data)

    def test_admin_registered_with_minimal_fields(self):
        self.assertIn(HomeHero, admin.site._registry)
        self.assertEqual(
            tuple(HomeHeroAdminForm.base_fields),
            ("title", "description", "media_type", "image", "video"),
        )

    def test_admin_prevents_second_configuration(self):
        request = SimpleNamespace(
            user=SimpleNamespace(has_perm=lambda *args, **kwargs: True)
        )
        model_admin = HomeHeroAdmin(HomeHero, admin.site)
        self.assertTrue(model_admin.has_add_permission(request))
        self.image_hero().save()
        self.assertFalse(model_admin.has_add_permission(request))

    def test_public_read_and_cache(self):
        self.image_hero().save()
        response = self.client.get("/api/content/home-hero/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "public, max-age=60")

    def test_public_writes_are_forbidden(self):
        for method in (self.client.post, self.client.put, self.client.patch, self.client.delete):
            with self.subTest(method=method.__name__):
                self.assertEqual(method("/api/content/home-hero/", {}).status_code, 405)


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA,
    CUSTOM_DRESS_MAX_IMAGE_SIZE_BYTES=1024 * 1024,
)
class CustomDressServiceTests(TestCase):
    def service(self, **overrides):
        data = {
            "title": "Une tenue conçue pour vous",
            "description": "Échangez avec notre responsable de confection.",
            "image": image_upload("robe.png"),
            "whatsapp_phone": "22370123456",
            "whatsapp_message": "Bonjour LobelStore, je souhaite une robe sur mesure.",
            "button_label": "Discuter sur WhatsApp",
            "availability_text": "Du lundi au samedi",
            "response_time_text": "Réponse habituelle sous 24 heures",
            "pricing_notice": "Le prix dépend du modèle et des matières.",
        }
        data.update(overrides)
        return CustomDressService(**data)

    def test_valid_creation_and_secure_filename(self):
        service = self.service()
        service.full_clean()
        service.save()
        self.assertNotIn("robe", service.image.name)
        self.assertTrue(service.image.name.startswith("content/custom-dress/"))

    def test_required_content(self):
        for field in ("title", "description", "image", "pricing_notice"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.service(**{field: ""}).full_clean()

    def test_image_validation_rejects_fake_svg_and_oversized(self):
        for upload in (
            SimpleUploadedFile("fake.png", b"not-image", content_type="image/png"),
            SimpleUploadedFile("dress.svg", b"<svg/>", content_type="image/svg+xml"),
        ):
            with self.subTest(upload=upload.name), self.assertRaises(ValidationError):
                self.service(image=upload).full_clean()
        with override_settings(CUSTOM_DRESS_MAX_IMAGE_SIZE_BYTES=4):
            with self.assertRaises(ValidationError):
                self.service().full_clean()

    def test_phone_validation(self):
        for value in ("22370123456", "2250700000000"):
            validate_whatsapp_phone(value)
        for value in (
            "1234567", "1" * 16, "223 70123456", "+22370123456",
            "223ABC12345", "https://wa.me/22370123456",
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_whatsapp_phone(value)

    def test_active_requires_message_and_phone(self):
        for field in ("whatsapp_message", "whatsapp_phone"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.service(is_active=True, **{field: ""}).full_clean()

    def test_plain_text_only(self):
        with self.assertRaises(ValidationError):
            self.service(description="<strong>Robe</strong>").full_clean()

    def test_activation_replaces_previous_service(self):
        first = self.service(title="Premier", is_active=True)
        first.full_clean()
        first.save()
        second = self.service(title="Second", is_active=True)
        second.full_clean(exclude=["is_active"])
        second.save()
        first.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)

    def test_endpoint_contract_is_public_and_absolute(self):
        service = self.service(is_active=True)
        service.full_clean()
        service.save()
        response = self.client.get("/api/content/custom-dress-service/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "public, max-age=60")
        data = response.json()
        self.assertTrue(data["image_url"].startswith("http://testserver/media/"))
        self.assertEqual(len(data["steps"]), 4)
        for field in ("id", "is_active", "created_at", "updated_at"):
            self.assertNotIn(field, data)

    def test_inactive_or_missing_returns_204(self):
        response = self.client.get("/api/content/custom-dress-service/")
        self.assertEqual(response.status_code, 204)
        self.service(is_active=False).save()
        self.assertEqual(
            self.client.get("/api/content/custom-dress-service/").status_code, 204
        )

    def test_writes_forbidden(self):
        for method in (self.client.post, self.client.put, self.client.patch, self.client.delete):
            with self.subTest(method=method.__name__):
                self.assertEqual(
                    method("/api/content/custom-dress-service/", {}).status_code, 405
                )

    def test_admin_registered(self):
        self.assertIn(CustomDressService, admin.site._registry)

    def test_admin_form_persists_whatsapp_phone_modification(self):
        service = self.service(is_active=True)
        service.full_clean()
        service.save()
        original_values = {
            "title": service.title,
            "description": service.description,
            "whatsapp_message": service.whatsapp_message,
            "button_label": service.button_label,
            "availability_text": service.availability_text,
            "response_time_text": service.response_time_text,
            "pricing_notice": service.pricing_notice,
            "is_active": service.is_active,
        }
        form = CustomDressServiceAdminForm(
            instance=service,
            data={
                **original_values,
                "whatsapp_phone": "2250700000000",
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        service.refresh_from_db()

        self.assertEqual(service.whatsapp_phone, "2250700000000")
        for field_name, expected in original_values.items():
            with self.subTest(field=field_name):
                self.assertEqual(getattr(service, field_name), expected)

    def test_api_returns_updated_whatsapp_phone_on_new_request(self):
        service = self.service(is_active=True)
        service.full_clean()
        service.save()

        first_response = self.client.get("/api/content/custom-dress-service/")
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.json()["whatsapp_phone"], "22370123456")

        service.whatsapp_phone = "2250700000000"
        service.full_clean()
        service.save()

        second_response = self.client.get("/api/content/custom-dress-service/")
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            second_response.json()["whatsapp_phone"], "2250700000000"
        )
        self.assertNotContains(second_response, "22370123456")
        self.assertEqual(second_response["Cache-Control"], "public, max-age=60")
