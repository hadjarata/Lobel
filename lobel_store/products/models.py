from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    video = models.FileField(upload_to='product_videos/', blank=True, null=True, help_text="Vidéo de présentation du produit")
    date_created = models.DateTimeField(auto_now_add=True)
    
    # Champs pour la page d'accueil
    sales_count = models.PositiveIntegerField(default=0, help_text="Nombre de ventes pour les best sellers")

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-date_created']


class ProductMedia(models.Model):
    """Modèle pour stocker plusieurs images et vidéos par produit"""
    
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Vidéo'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='media_files')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='product_media/')
    order = models.PositiveIntegerField(default=0, help_text="Ordre d'affichage")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"{self.product.name} - {self.get_media_type_display()} ({self.order})"
    
    @property
    def is_image(self):
        return self.media_type == 'image'
    
    @property
    def is_video(self):
        return self.media_type == 'video'