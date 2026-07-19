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
            'created_at',
            'format',
            'mime_type',
            'size_bytes',
            'width',
            'height',
            'duration_seconds',
            'checksum',
            'is_active',
        ]
        read_only_fields = [
            'created_at', 'format', 'mime_type', 'size_bytes', 'width', 'height',
            'duration_seconds', 'checksum', 'is_active',
        ]

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
        fields = ['id', 'name', 'description', 'is_active', 'date_created']


# =========================
# PRODUCT VARIANT
# =========================
class ProductVariantSerializer(serializers.ModelSerializer):
    color = ColorSerializer()
    size = SizeSerializer()

    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'size', 'stock', 'is_active', 'sku', 'price']


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
            'is_active',
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


def _absolute_file_url(serializer, media):
    if not media or not media.file:
        return None
    request = serializer.context.get("request")
    return request.build_absolute_uri(media.file.url) if request else media.file.url


class PublicMediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductMedia
        fields = ["id", "media_type", "url", "order", "width", "height", "duration_seconds"]

    def get_url(self, obj):
        return _absolute_file_url(self, obj)


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    collections = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "price", "sales_count", "date_created", "category",
            "collections", "variants", "image", "is_available",
        ]

    def get_collections(self, obj):
        return [item.pk for item in getattr(obj, "prefetched_collections", ())]

    def get_variants(self, obj):
        return ProductVariantSerializer(
            getattr(obj, "prefetched_active_variants", ()), many=True, context=self.context
        ).data

    def get_image(self, obj):
        media = next(iter(getattr(obj, "prefetched_active_media", ())), None)
        return _absolute_file_url(self, media)


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    collections = serializers.SerializerMethodField()
    media_files = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "category", "description", "price", "sales_count",
            "is_active", "date_created", "collections", "media_files", "variants",
            "image", "video", "is_available",
        ]

    def _media(self, obj, media_type):
        return next(
            (item for item in getattr(obj, "prefetched_active_media", ()) if item.media_type == media_type),
            None,
        )

    def get_collections(self, obj):
        return [item.pk for item in getattr(obj, "prefetched_collections", ())]

    def get_media_files(self, obj):
        return PublicMediaSerializer(
            getattr(obj, "prefetched_active_media", ()), many=True, context=self.context
        ).data

    def get_variants(self, obj):
        return ProductVariantSerializer(
            getattr(obj, "prefetched_active_variants", ()), many=True, context=self.context
        ).data

    def get_image(self, obj):
        return _absolute_file_url(self, self._media(obj, "image"))

    def get_video(self, obj):
        return _absolute_file_url(self, self._media(obj, "video"))


class ProductMediaCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    media_type = serializers.ChoiceField(choices=ProductMedia.MEDIA_TYPES)
    file = serializers.FileField()
    order = serializers.IntegerField(min_value=0, default=0)

    def create(self, validated_data):
        from .media_services import CatalogMediaService
        return CatalogMediaService.add(
            product=validated_data["product"],
            media_type=validated_data["media_type"],
            upload=validated_data["file"],
            order=validated_data["order"],
            actor=self.context["request"].user,
        )

    def to_representation(self, instance):
        return ProductMediaSerializer(instance, context=self.context).data


class ProductMediaUpdateSerializer(serializers.Serializer):
    file = serializers.FileField()

    def update(self, instance, validated_data):
        from .media_services import CatalogMediaService
        return CatalogMediaService.replace(
            media=instance,
            upload=validated_data["file"],
            actor=self.context["request"].user,
        )

    def to_representation(self, instance):
        return ProductMediaSerializer(instance, context=self.context).data


class ProductWriteSerializer(serializers.ModelSerializer):
    """Minimal catalogue input accepted from staff users."""

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    collections = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'description',
            'price',
            'is_active',
            'collections',
        ]

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

    def validate(self, attrs):
        from .media_validation import validate_image_upload, validate_video_upload
        cover_type = attrs.get("cover_type", getattr(self.instance, "cover_type", Collection.COVER_TYPE_IMAGE))
        image = attrs.get("image")
        video = attrs.get("video")
        if image and cover_type == Collection.COVER_TYPE_IMAGE:
            validate_image_upload(image)
        if video and cover_type == Collection.COVER_TYPE_VIDEO:
            validate_video_upload(video)
        return attrs
