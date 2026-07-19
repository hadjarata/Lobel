from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from .media_validation import validate_video_upload


class VideoValidationTests(SimpleTestCase):
    def test_non_mp4_and_renamed_text_are_rejected(self):
        with self.assertRaises(ValidationError):
            validate_video_upload(SimpleUploadedFile("clip.webm", b"not video"))
        with patch("products.media_validation.shutil.which", return_value=None):
            with self.assertRaises(ValidationError):
                validate_video_upload(SimpleUploadedFile("clip.mp4", b"not video"))

    @override_settings(MAX_VIDEO_UPLOAD_BYTES=2)
    def test_video_size_limit_precedes_probe(self):
        with self.assertRaises(ValidationError):
            validate_video_upload(SimpleUploadedFile("clip.mp4", b"123"))
