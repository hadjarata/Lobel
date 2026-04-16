from rest_framework import serializers
from .models import Category, Product, ProductMedia


class ProductMediaSerializer(serializers.ModelSerializer):
    """Serializer pour les médias de produits"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductMedia
        fields = ['id', 'media_type', 'file', 'file_url', 'order', 'created_at']
        read_only_fields = ['created_at']
    
    def get_file_url(self, obj):
        """Retourne l'URL complète du fichier"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'date_created']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()  # nested serializer pour afficher la catégorie
    media = ProductMediaSerializer(many=True, read_only=True)  # médias multiples
    image = serializers.SerializerMethodField()  # Compatibilité frontend
    video = serializers.SerializerMethodField()  # Compatibilité frontend

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'description', 'price', 'stock', 
            'date_created', 'sales_count', 'media', 'image', 'video'
        ]
    
    def get_image(self, obj):
        """Retourne la première image des médias pour compatibilité"""
        first_image = obj.media_files.filter(media_type='image').first()
        if first_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.file.url)
            return first_image.file.url
        return None
    
    def get_video(self, obj):
        """Retourne la première vidéo des médias pour compatibilité"""
        first_video = obj.media_files.filter(media_type='video').first()
        if first_video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_video.file.url)
            return first_video.file.url
        return None