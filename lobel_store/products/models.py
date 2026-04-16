from django.db import models


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