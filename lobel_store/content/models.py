import uuid
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from products.media_validation import validate_image_upload, validate_video_upload


def hero_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"content/home-hero/{uuid.uuid4().hex}{extension}"


def custom_dress_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"content/custom-dress/{uuid.uuid4().hex}{extension}"


def validate_whatsapp_phone(value):
    value = value or ""
    if not value.isascii() or not value.isdigit() or not 8 <= len(value) <= 15:
        raise ValidationError(
            "Saisissez 8 à 15 chiffres au format international, sans +, espace ni tiret."
        )


def validate_plain_text(value):
    if "<" in value or ">" in value:
        raise ValidationError("Utilisez uniquement du texte brut, sans balise HTML.")


def validate_button_url(value):
    """Compatibilité avec la migration historique content.0001."""
    value = (value or "").strip()
    if not value:
        return
    if value.startswith("/") and not value.startswith("//"):
        return
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc and not parsed.username:
        return
    raise ValidationError(
        "Utilisez un chemin interne commençant par / ou une URL HTTPS."
    )


class HomeHero(models.Model):
    MEDIA_IMAGE = "IMAGE"
    MEDIA_VIDEO = "VIDEO"
    MEDIA_CHOICES = (
        (MEDIA_IMAGE, "Image"),
        (MEDIA_VIDEO, "Vidéo"),
    )

    title = models.CharField(
        "titre", max_length=180, default="Bienvenue sur LobelStore"
    )
    description = models.TextField(
        "description",
        max_length=600,
        default=(
            "Découvrez notre sélection de créations et explorez notre boutique."
        ),
    )
    media_type = models.CharField(
        "type de couverture",
        max_length=10,
        choices=MEDIA_CHOICES,
        default=MEDIA_IMAGE,
    )
    image = models.ImageField(
        "image",
        upload_to=hero_upload_to,
        blank=True,
        null=True,
        help_text="JPEG, PNG ou WebP. Obligatoire pour une couverture image.",
    )
    video = models.FileField(
        "vidéo",
        upload_to=hero_upload_to,
        blank=True,
        null=True,
        help_text="MP4 H.264. Obligatoire pour une couverture vidéo.",
    )

    class Meta:
        verbose_name = "couverture de l'accueil"
        verbose_name_plural = "couverture de l'accueil"
        constraints = [
            models.UniqueConstraint(
                models.Value(1), name="single_home_hero_configuration"
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}
        if self.media_type == self.MEDIA_IMAGE:
            if not self.image:
                errors["image"] = "Une image est obligatoire."
            if self.video:
                errors["video"] = "La vidéo doit être vide pour une couverture image."
        elif self.media_type == self.MEDIA_VIDEO:
            if not self.video:
                errors["video"] = "Une vidéo MP4 est obligatoire."
            if self.image:
                errors["image"] = "L'image doit être vide pour une couverture vidéo."
        if self.image and not getattr(self.image, "_committed", True):
            if self.image.size > settings.HOME_HERO_MAX_IMAGE_SIZE_BYTES:
                errors["image"] = "Image trop volumineuse."
            else:
                try:
                    validate_image_upload(self.image)
                except ValidationError as exc:
                    errors["image"] = exc.messages
        if self.video and not getattr(self.video, "_committed", True):
            if self.video.size > settings.HOME_HERO_MAX_VIDEO_SIZE_BYTES:
                errors["video"] = "Vidéo trop volumineuse."
            else:
                try:
                    validate_video_upload(self.video)
                except ValidationError as exc:
                    errors["video"] = exc.messages
        if errors:
            raise ValidationError(errors)

class CustomDressService(models.Model):
    title = models.CharField(max_length=180)
    description = models.TextField(max_length=1000, validators=[validate_plain_text])
    image = models.ImageField(
        upload_to=custom_dress_upload_to,
        help_text="JPEG, PNG ou WebP.",
    )
    whatsapp_phone = models.CharField(
        max_length=15,
        validators=[validate_whatsapp_phone],
        help_text="8 à 15 chiffres au format international, sans +, espace ni tiret.",
    )
    whatsapp_message = models.TextField(
        max_length=1000,
        validators=[validate_plain_text],
        help_text="Message générique uniquement : aucune donnée personnelle.",
    )
    button_label = models.CharField(
        max_length=80, default="Discuter sur WhatsApp"
    )
    availability_text = models.CharField(max_length=240, blank=True)
    response_time_text = models.CharField(max_length=240, blank=True)
    pricing_notice = models.CharField(max_length=400, validators=[validate_plain_text])
    is_active = models.BooleanField(
        default=False,
        help_text="L'activation désactive automatiquement l'ancienne configuration.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("is_active",),
                condition=models.Q(is_active=True),
                name="unique_active_custom_dress_service",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}
        if self.is_active and not self.whatsapp_message.strip():
            errors["whatsapp_message"] = "Le message est obligatoire pour un service actif."
        if self.is_active and not self.whatsapp_phone:
            errors["whatsapp_phone"] = "Le numéro est obligatoire pour un service actif."
        if self.image and not getattr(self.image, "_committed", True):
            if self.image.size > settings.CUSTOM_DRESS_MAX_IMAGE_SIZE_BYTES:
                errors["image"] = "Image trop volumineuse."
            else:
                try:
                    validate_image_upload(self.image)
                except ValidationError as exc:
                    errors["image"] = exc.messages
        if errors:
            raise ValidationError(errors)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.is_active:
            type(self).objects.select_for_update().filter(
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
