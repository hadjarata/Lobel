from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    Category,
    Product,
    ProductMedia,
    Color,
    Size,
    ProductVariant
)

# =========================
# MEDIA INLINE
# =========================
class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ('media_type', 'file', 'order')
    ordering = ('order',)


# =========================
# VARIANT INLINE (COULEUR + TAILLE)
# =========================
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('color', 'size', 'stock')


# =========================
# CATEGORY ADMIN
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_created')
    search_fields = ('name',)
    ordering = ('-date_created',)


# =========================
# COLOR ADMIN (1 clic)
# =========================
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')
    search_fields = ('name',)


# =========================
# SIZE ADMIN (1 clic)
# =========================
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# =========================
# PRODUCT ADMIN (ULTRA CLEAN)
# =========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
        'sales_count',
        'date_created'
    )

    list_filter = ('category', 'date_created')
    search_fields = ('name', 'description')
    ordering = ('-date_created',)
    readonly_fields = ('date_created',)

    inlines = [
        ProductMediaInline,
        ProductVariantInline   # 🔥 AJOUT IMPORTANT
    ]

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'category', 'description')
        }),
        ('Prix & ventes', {
            'fields': ('price', 'sales_count')
        }),
        ('Système', {
            'fields': ('date_created',),
            'classes': ('collapse',)
        }),
    )

    # =========================
    # VALIDATION SIMPLE
    # =========================
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.media_files.count() == 0:
            messages.warning(
                request,
                "⚠ Ce produit n'a aucun média (image ou vidéo)."
            )

        if obj.variants.count() == 0:
            messages.warning(
                request,
                "⚠ Ce produit n'a aucune variante (couleur/taille)."
            )