from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductMedia,
    ProductVariant,
    Color,
    Size
)


# =========================
# COLOR
# =========================
class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'hex_code']


# =========================
# SIZE
# =========================
class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'name']


# =========================
# PRODUCT MEDIA
# =========================
class ProductMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductMedia
        fields = [
            'id',
            'media_type',
            'file',
            'file_url',
            'order',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def get_file_url(self, obj):
        """Retourne l'URL complète du fichier"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


# =========================
# CATEGORY
# =========================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'date_created']


# =========================
# PRODUCT VARIANT
# =========================
class ProductVariantSerializer(serializers.ModelSerializer):
    color = ColorSerializer()
    size = SizeSerializer()

    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'size', 'stock']


# =========================
# PRODUCT (MAIN SERIALIZER)
# =========================
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    # médias multiples
    media_files = ProductMediaSerializer(many=True, read_only=True)

    # variantes produit (couleur + taille + stock)
    variants = ProductVariantSerializer(many=True, read_only=True)

    # compatibilité frontend (ancien système)
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'category',
            'description',
            'price',
            'sales_count',
            'date_created',

            # nouveau système
            'media_files',
            'variants',

            # compatibilité ancienne UI
            'image',
            'video'
        ]

    def get_image(self, obj):
        """Retourne la première image pour compatibilité frontend"""
        first_image = obj.media_files.filter(media_type='image').first()
        if first_image:
            request = self.context.get('request')
            return request.build_absolute_uri(first_image.file.url) if request else first_image.file.url
        return None

    def get_video(self, obj):
        """Retourne la première vidéo pour compatibilité frontend"""
        first_video = obj.media_files.filter(media_type='video').first()
        if first_video:
            request = self.context.get('request')
            return request.build_absolute_uri(first_video.file.url) if request else first_video.file.url
        return None