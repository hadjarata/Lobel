from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

# Create your views here.
# products/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from orders import models
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, ProductWriteSerializer
from .models import Collection
from .serializers import CollectionSerializer
from .permissions import IsAdminOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductWriteSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all().prefetch_related('collections')
        collection_slug = self.request.query_params.get('collection')

        if collection_slug:
            queryset = queryset.filter(collections__slug=collection_slug).distinct()

        return queryset
    
    @action(detail=False, methods=['get'])
    def new(self, request):
        """Retourne les nouveautés (créées il y a moins de 30 jours)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_products = Product.objects.filter(date_created__gte=thirty_days_ago).order_by('-date_created')[:8]
        serializer = self.get_serializer(new_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        """Retourne les best sellers (produits les plus vendus)"""
        best_sellers = Product.objects.filter(sales_count__gt=0).order_by('-sales_count')[:8]
        serializer = self.get_serializer(best_sellers, many=True)
        return Response(serializer.data)
    
class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.filter(is_active=True)
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'  # 🔥 IMPORTANT

    def get_queryset(self):
        """Optionnel : filtrer par date (collections actives dans le temps)"""
        today = timezone.now().date()
        return Collection.objects.filter(
            is_active=True
        ).filter(
            Q(start_date__lte=today) | Q(start_date__isnull=True),
            Q(end_date__gte=today) | Q(end_date__isnull=True),
        )
