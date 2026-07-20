from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max, Min, Q

# Create your views here.
# products/views.py
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.throttling import ScopedRateThrottle

from orders import models
from .models import Category, Color, Product, ProductMedia, ProductVariant, Size
from .serializers import (
    CategorySerializer, ProductSerializer, ProductWriteSerializer,
    ProductMediaSerializer, ProductMediaCreateSerializer, ProductMediaUpdateSerializer,
    ProductListSerializer, ProductDetailSerializer, PublicMediaSerializer,
    ColorSerializer, SizeSerializer,
)
from .models import Collection
from .serializers import CollectionSerializer
from .permissions import IsAdminOrReadOnly, IsCatalogMediaManager
from .services import CatalogueArchiveService
from .media_services import CatalogMediaService
from .querysets import product_queryset
from .filters import ProductQueryFilter
from django.conf import settings

archive_service = CatalogueArchiveService()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Category.objects.order_by("name", "id")
        return Category.objects.filter(is_active=True).order_by("name", "id")

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        category = archive_service.archive_category(self.get_object())
        return Response(self.get_serializer(category).data)

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        category = archive_service.reactivate_category(self.get_object())
        return Response(self.get_serializer(category).data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [ProductQueryFilter]
    max_search_length = settings.API_MAX_SEARCH_LENGTH

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductWriteSerializer
        if self.action in ("list", "new", "bestsellers"):
            return ProductListSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        public = not (self.request.user.is_authenticated and self.request.user.is_staff)
        return product_queryset(public=public, detail=self.action not in ("list", "new", "bestsellers"))

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        product = archive_service.archive_product(self.get_object())
        product = product_queryset(public=False, detail=True).get(pk=product.pk)
        return Response(ProductDetailSerializer(product, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        try:
            product = archive_service.reactivate_product(self.get_object())
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        product = product_queryset(public=False, detail=True).get(pk=product.pk)
        return Response(ProductDetailSerializer(product, context={"request": request}).data)
    
    @action(detail=False, methods=['get'])
    def new(self, request):
        """Retourne les nouveautés (créées il y a moins de 30 jours)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        products = self.filter_queryset(self.get_queryset().filter(date_created__gte=thirty_days_ago))
        page = self.paginate_queryset(products)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        """Retourne les best sellers (produits les plus vendus)"""
        products = self.filter_queryset(
            self.get_queryset().filter(sales_count__gt=0).order_by("-sales_count", "-id")
        )
        page = self.paginate_queryset(products)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="filter-options")
    def filter_options(self, request):
        """Return complete public filter facets, independently of the current page."""
        today = timezone.now().date()
        products = product_queryset(public=True, detail=False)
        product_ids = products.order_by().values("pk")
        variants = ProductVariant.objects.filter(
            product_id__in=product_ids,
            product__is_active=True,
            product__category__is_active=True,
            is_active=True,
            stock__gt=0,
        )
        categories = Category.objects.filter(
            is_active=True, products__in=product_ids
        ).distinct().order_by("name", "id")
        collections = Collection.objects.filter(
            is_active=True, products__in=product_ids
        ).filter(
            Q(start_date__lte=today) | Q(start_date__isnull=True),
            Q(end_date__gte=today) | Q(end_date__isnull=True),
        ).distinct().order_by("name", "id")
        colors = Color.objects.filter(
            productvariant__in=variants, productvariant__color__isnull=False
        ).distinct().order_by("name", "id")
        sizes = Size.objects.filter(
            productvariant__in=variants, productvariant__size__isnull=False
        ).distinct().order_by("name", "id")
        price_range = products.aggregate(min=Min("price"), max=Max("price"))

        return Response({
            "categories": CategorySerializer(categories, many=True).data,
            "collections": [
                {"id": item.id, "name": item.name, "slug": item.slug}
                for item in collections
            ],
            "colors": ColorSerializer(colors, many=True).data,
            "sizes": SizeSerializer(sizes, many=True).data,
            "price": {
                "min": str(price_range["min"]) if price_range["min"] is not None else None,
                "max": str(price_range["max"]) if price_range["max"] is not None else None,
            },
        })

    @action(
        detail=False,
        methods=["post"],
        url_path="resolve-variants",
        permission_classes=[permissions.AllowAny],
    )
    def resolve_variants(self, request):
        ids = request.data.get("variant_ids")
        if (
            not isinstance(ids, list) or not ids or len(ids) > 50
            or any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in ids)
        ):
            return Response(
                {"code": "invalid_variant_ids", "detail": "variant_ids doit contenir 1 à 50 identifiants."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        unique_ids = list(dict.fromkeys(ids))
        variants = ProductVariant.objects.select_related(
            "product", "color", "size"
        ).prefetch_related("product__media_files").filter(pk__in=unique_ids)
        by_id = {variant.pk: variant for variant in variants}
        results = []
        for variant_id in unique_ids:
            variant = by_id.get(variant_id)
            if variant is None:
                continue
            image = next(
                (
                    media for media in variant.product.media_files.all()
                    if media.is_active and media.media_type == "image"
                ),
                None,
            )
            results.append({
                "id": variant.id,
                "product_id": variant.product_id,
                "product_name": variant.product.name,
                "sku": variant.sku,
                "color": ColorSerializer(variant.color).data if variant.color else None,
                "size": SizeSerializer(variant.size).data if variant.size else None,
                "attributes": {},
                "price": str(variant.effective_price),
                "stock": variant.stock,
                "is_available": bool(
                    variant.is_active and variant.product.is_active and variant.stock > 0
                ),
                "image": (
                    request.build_absolute_uri(image.file.url) if image and image.file else None
                ),
            })
        return Response({"results": results, "missing_ids": [
            variant_id for variant_id in unique_ids if variant_id not in by_id
        ]})
    
class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.filter(is_active=True)
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'  # 🔥 IMPORTANT

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_queryset(self):
        """Optionnel : filtrer par date (collections actives dans le temps)"""
        today = timezone.now().date()
        return Collection.objects.filter(
            is_active=True
        ).filter(
            Q(start_date__lte=today) | Q(start_date__isnull=True),
            Q(end_date__gte=today) | Q(end_date__isnull=True),
        ).prefetch_related("products").order_by("-created_at", "-id")


class ProductMediaViewSet(viewsets.ModelViewSet):
    queryset = ProductMedia.objects.select_related("product")
    permission_classes = [IsCatalogMediaManager]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "catalog_media_upload"
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = self.queryset
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True, product__is_active=True)
        product_id = self.request.query_params.get("product")
        queryset = queryset.order_by("order", "id")
        return queryset.filter(product_id=product_id) if product_id else queryset

    def get_serializer_class(self):
        if self.action == "create":
            return ProductMediaCreateSerializer
        if self.action == "partial_update":
            return ProductMediaUpdateSerializer
        return PublicMediaSerializer

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        media = CatalogMediaService.archive(self.get_object())
        return Response(ProductMediaSerializer(media, context={"request": request}).data)
