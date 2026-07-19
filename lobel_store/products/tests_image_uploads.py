from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from .media_validation import validate_image_upload
from .tests_media_helpers import image_upload


class ImageValidationTests(SimpleTestCase):
    def test_jpeg_png_and_webp_are_decoded_and_cursor_reset(self):
        for name, image_format in (("a.jpg", "JPEG"), ("a.png", "PNG"), ("a.webp", "WEBP")):
            with self.subTest(image_format=image_format):
                upload = image_upload(name, image_format)
                metadata = validate_image_upload(upload)
                self.assertEqual(metadata["format"], image_format)
                self.assertEqual(upload.tell(), 0)

    def test_content_type_is_not_trusted(self):
        fake = SimpleUploadedFile("evil.jpg", b"MZ executable", content_type="image/jpeg")
        with self.assertRaises(ValidationError):
            validate_image_upload(fake)

    def test_svg_traversal_extension_mismatch_and_corruption_are_rejected(self):
        invalid = [
            SimpleUploadedFile("../../evil.svg", b"<svg/>", content_type="image/svg+xml"),
            image_upload("wrong.jpg", "PNG"),
            SimpleUploadedFile("broken.png", b"\x89PNG\r\n\x1a\nbroken", content_type="image/png"),
        ]
        for upload in invalid:
            with self.assertRaises(ValidationError):
                validate_image_upload(upload)

    @override_settings(MAX_IMAGE_UPLOAD_BYTES=2)
    def test_size_limit_is_applied_before_decode(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(image_upload())

    @override_settings(MAX_IMAGE_WIDTH=4, MAX_IMAGE_HEIGHT=4, MAX_IMAGE_PIXELS=16)
    def test_dimensions_and_pixels_are_limited(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(image_upload(size=(8, 8)))

    def test_server_generates_canonical_uuid_name(self):
        upload = image_upload("../../client controlled.png")
        validate_image_upload(upload)
        self.assertRegex(upload.name, r"^[0-9a-f]{32}\.png$")
