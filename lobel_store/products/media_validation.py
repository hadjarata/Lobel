import hashlib
import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

IMAGE_FORMATS = {"JPEG": (".jpg", "image/jpeg"), "PNG": (".png", "image/png"), "WEBP": (".webp", "image/webp")}
IMAGE_EXTENSIONS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def _metadata(upload):
    digest = hashlib.sha256()
    upload.seek(0)
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    return upload.size, digest.hexdigest()


def validate_image_upload(upload):
    size, checksum = _metadata(upload)
    if size > settings.MAX_IMAGE_UPLOAD_BYTES:
        raise ValidationError("file_too_large")
    extension = Path(upload.name).suffix.lower()
    if extension not in IMAGE_EXTENSIONS:
        raise ValidationError("unsupported_media_type")
    try:
        upload.seek(0)
        with Image.open(upload) as image:
            detected = image.format
            image.verify()
        upload.seek(0)
        with Image.open(upload) as image:
            image.load()
            width, height = image.size
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ValidationError("invalid_image") from exc
    finally:
        upload.seek(0)
    if detected not in IMAGE_FORMATS or IMAGE_EXTENSIONS[extension] != detected:
        raise ValidationError("unsupported_media_type")
    if width > settings.MAX_IMAGE_WIDTH or height > settings.MAX_IMAGE_HEIGHT or width * height > settings.MAX_IMAGE_PIXELS:
        raise ValidationError("image_dimensions_exceeded")
    suffix, mime = IMAGE_FORMATS[detected]
    upload.name = f"{uuid.uuid4().hex}{suffix}"
    return {"format": detected, "mime_type": mime, "size_bytes": size, "width": width, "height": height, "checksum": checksum}


def validate_video_upload(upload):
    size, checksum = _metadata(upload)
    if size > settings.MAX_VIDEO_UPLOAD_BYTES:
        raise ValidationError("file_too_large")
    if Path(upload.name).suffix.lower() != ".mp4":
        raise ValidationError("unsupported_media_type")
    executable = settings.FFPROBE_PATH or shutil.which("ffprobe")
    if not executable:
        raise ValidationError("invalid_video: ffprobe is required")
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temporary:
            temporary_name = temporary.name
            upload.seek(0)
            for chunk in upload.chunks():
                temporary.write(chunk)
        result = subprocess.run(
            [executable, "-v", "error", "-show_streams", "-show_format", "-of", "json", temporary_name],
            capture_output=True, text=True, timeout=settings.FFPROBE_TIMEOUT_SECONDS, check=True, shell=False,
        )
        probe = json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as exc:
        raise ValidationError("invalid_video") from exc
    finally:
        upload.seek(0)
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
    streams = probe.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    if len(videos) != 1 or len(streams) > settings.MAX_VIDEO_TRACKS:
        raise ValidationError("invalid_video")
    stream = videos[0]
    formats = set(probe.get("format", {}).get("format_name", "").split(","))
    if not formats.intersection({"mov", "mp4", "m4a", "3gp", "3g2", "mj2"}) or stream.get("codec_name") != "h264":
        raise ValidationError("unsupported_media_type")
    width, height = int(stream.get("width", 0)), int(stream.get("height", 0))
    duration = float(stream.get("duration") or probe.get("format", {}).get("duration") or 0)
    if not duration or duration > settings.MAX_VIDEO_DURATION_SECONDS:
        raise ValidationError("video_duration_exceeded")
    if width > settings.MAX_VIDEO_WIDTH or height > settings.MAX_VIDEO_HEIGHT:
        raise ValidationError("video_dimensions_exceeded")
    upload.name = f"{uuid.uuid4().hex}.mp4"
    return {"format": "MP4", "mime_type": "video/mp4", "size_bytes": size, "width": width, "height": height, "duration_seconds": duration, "checksum": checksum}
