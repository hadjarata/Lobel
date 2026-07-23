from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from pathlib import Path
import uuid

from .media_validation import validate_image_upload, validate_video_upload
from store.money import validate_xof_integer


def product_media_upload_to(instance, filename):
    return f"products/{instance.product_id}/media/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


def collection_image_upload_to(instance, filename):
    return f"collections/{instance.pk or 'new'}/images/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


def collection_video_upload_to(instance, filename):
    return f"collections/{instance.pk or 'new'}/videos/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


# =========================
# CATEGORY
# =========================
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# =========================
# PRODUCT (CLEAN)
# =========================
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[validate_xof_integer]
    )
    
    date_created = models.DateTimeField(auto_now_add=True)

    # best sellers logic
    sales_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    collections = models.ManyToManyField(
    'Collection',
    related_name='products',
    blank=True
)

    class Meta:
        ordering = ['-date_created']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price=models.functions.Floor("price")),
                name="product_price_xof_integer",
            ),
        ]

    def __str__(self):
        return self.name


# =========================
# PRODUCT MEDIA (MULTI IMAGES / VIDEOS)
# =========================
class ProductMedia(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to=product_media_upload_to)
    
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    format = models.CharField(max_length=16, blank=True)
    mime_type = models.CharField(max_length=64, blank=True)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration_seconds = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.media_type}"


    def clean(self):
        super().clean()
        if self.file and not getattr(self.file, "_committed", True):
            validator = validate_image_upload if self.media_type == "image" else validate_video_upload
            for key, value in validator(self.file).items():
                setattr(self, key, value)


# =========================
# COLOR
# =========================
class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, blank=True, null=True)

    def __str__(self):
        return self.name


# =========================
# SIZE
# =========================
class Size(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


# =========================
# PRODUCT VARIANT (CORE E-COMMERCE)
# =========================
class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    size = models.ForeignKey(
        Size,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[validate_xof_integer],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("product", "color", "size"),
                name="unique_product_color_size_variant",
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name="variant_stock_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(price__isnull=True)
                    | models.Q(price=models.functions.Floor("price"))
                ),
                name="variant_price_xof_integer",
            ),
        ]

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.product.price

    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"
    
    # Collections


class Collection(models.Model):
    COVER_TYPE_IMAGE = 'image'
    COVER_TYPE_VIDEO = 'video'
    COVER_TYPE_CHOICES = [
        (COVER_TYPE_IMAGE, 'Image'),
        (COVER_TYPE_VIDEO, 'Video'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_type = models.CharField(
        max_length=10,
        choices=COVER_TYPE_CHOICES,
        default=COVER_TYPE_IMAGE,
    )

    image = models.ImageField(upload_to=collection_image_upload_to, blank=True, null=True)
    video = models.FileField(upload_to=collection_video_upload_to, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    format = models.CharField(max_length=16, blank=True)
    mime_type = models.CharField(max_length=64, blank=True)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration_seconds = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.cover_type == self.COVER_TYPE_IMAGE:
            self.video = None

            if not self.image:
                raise ValidationError({
                    'image': "An image is required when cover type is set to image."
                })
            elif not getattr(self.image, "_committed", True):
                for key, value in validate_image_upload(self.image).items():
                    setattr(self, key, value)

        elif self.cover_type == self.COVER_TYPE_VIDEO:
            self.image = None

            if not self.video:
                raise ValidationError({
                    'video': "A video is required when cover type is set to video."
                })
            elif not getattr(self.video, "_committed", True):
                for key, value in validate_video_upload(self.video).items():
                    setattr(self, key, value)

        else:
            raise ValidationError({
                'cover_type': "Invalid cover type selected."
            })

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Collection.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
