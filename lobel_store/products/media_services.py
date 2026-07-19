import logging

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Product, ProductMedia

logger = logging.getLogger(__name__)


class CatalogMediaService:
    @staticmethod
    @transaction.atomic
    def add(*, product, media_type, upload, order=0, actor=None):
        locked = Product.objects.select_for_update().get(pk=product.pk)
        maximum = settings.MAX_PRODUCT_IMAGES if media_type == "image" else settings.MAX_PRODUCT_VIDEOS
        if locked.media_files.filter(media_type=media_type, is_active=True).count() >= maximum:
            raise ValidationError({"file": "media_quota_exceeded"})
        media = ProductMedia(product=locked, media_type=media_type, file=upload, order=order)
        try:
            media.full_clean()
            media.save()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc
        except Exception:
            if media.file and media.file.name:
                media.file.storage.delete(media.file.name)
            raise
        logger.info(
            "catalog.media_uploaded actor_id=%s product_id=%s type=%s size=%s format=%s",
            getattr(actor, "pk", None), locked.pk, media_type, media.size_bytes, media.format,
        )
        return media

    @staticmethod
    @transaction.atomic
    def replace(*, media, upload, actor=None):
        media = ProductMedia.objects.select_for_update().get(pk=media.pk)
        old_name, storage = media.file.name, media.file.storage
        media.file = upload
        try:
            media.full_clean()
            media.save()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc
        except Exception:
            if media.file and media.file.name and media.file.name != old_name:
                media.file.storage.delete(media.file.name)
            raise
        transaction.on_commit(
            lambda: storage.delete(old_name)
            if old_name and not ProductMedia.objects.filter(file=old_name).exists()
            else None
        )
        logger.info("catalog.media_replaced actor_id=%s media_id=%s", getattr(actor, "pk", None), media.pk)
        return media

    @staticmethod
    def archive(media):
        media.is_active = False
        media.save(update_fields=["is_active"])
        return media
