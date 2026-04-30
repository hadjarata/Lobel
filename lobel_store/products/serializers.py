from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductMedia,
    ProductVariant,
    Color,
    Size,
    Collection
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
    collections = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all(),
        many=True,
        required=False
    )

    media_files = ProductMediaSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

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

            'collections',  # 🔥 AJOUT IMPORTANT

            'media_files',
            'variants',

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

class CollectionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    products = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'cover_type',
            'image',
            'image_url',
            'video',
            'video_url',
            'is_active',
            'start_date',
            'end_date',
            'products',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        """Retourne l'URL complète de l'image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_video_url(self, obj):
        """Retourne l'URL complète de la vidéo"""
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
            return obj.video.url
        return None
