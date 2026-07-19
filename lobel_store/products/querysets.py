from django.db.models import Exists, OuterRef, Prefetch

from .models import Collection, Product, ProductMedia, ProductVariant


def product_queryset(*, public, detail=False):
    queryset = Product.objects.select_related("category").annotate(
        is_available=Exists(
            ProductVariant.objects.filter(
                product_id=OuterRef("pk"), is_active=True, stock__gt=0
            )
        )
    )
    if public:
        queryset = queryset.filter(is_active=True, category__is_active=True)
    collections = Collection.objects.order_by("id")
    media = ProductMedia.objects.order_by("order", "id")
    variants = ProductVariant.objects.select_related("color", "size").order_by("id")
    if public:
        collections = collections.filter(is_active=True)
        media = media.filter(is_active=True)
        variants = variants.filter(is_active=True)
    if not detail:
        media = media.filter(media_type="image")
    return queryset.prefetch_related(
        Prefetch("collections", queryset=collections, to_attr="prefetched_collections"),
        Prefetch("media_files", queryset=media, to_attr="prefetched_active_media"),
        Prefetch("variants", queryset=variants, to_attr="prefetched_active_variants"),
    )
