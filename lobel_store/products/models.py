from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


# =========================
# CATEGORY
# =========================
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================
# PRODUCT (CLEAN)
# =========================
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    date_created = models.DateTimeField(auto_now_add=True)

    # best sellers logic
    sales_count = models.PositiveIntegerField(default=0)
    collections = models.ManyToManyField(
    'Collection',
    related_name='products',
    blank=True
)

    class Meta:
        ordering = ['-date_created']

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
    file = models.FileField(upload_to='product_media/')
    
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.media_type}"


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
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    size = models.ForeignKey(
        Size,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'color', 'size')

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

    image = models.ImageField(upload_to='collections/images/', blank=True, null=True)
    video = models.FileField(upload_to='collections/videos/', blank=True, null=True)

    is_active = models.BooleanField(default=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.cover_type == self.COVER_TYPE_IMAGE:
            self.video = None

            if not self.image:
                raise ValidationError({
                    'image': "An image is required when cover type is set to image."
                })

        elif self.cover_type == self.COVER_TYPE_VIDEO:
            self.image = None

            if not self.video:
                raise ValidationError({
                    'video': "A video is required when cover type is set to video."
                })

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
