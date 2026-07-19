from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def image_upload(name="test.png", image_format="PNG", size=(8, 8)):
    buffer = BytesIO()
    Image.new("RGB", size, (120, 30, 200)).save(buffer, format=image_format)
    mime = "image/jpeg" if image_format == "JPEG" else f"image/{image_format.lower()}"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=mime)
