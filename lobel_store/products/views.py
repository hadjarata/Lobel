from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

# Create your views here.
# products/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from rest_framework.permissions import AllowAny


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
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