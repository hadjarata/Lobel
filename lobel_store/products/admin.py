from django import forms
from django.contrib import admin, messages
from django.conf import settings
from django.utils.html import format_html
from .models import (
    Category,
    Collection,
    Product,
    ProductMedia,
    ProductVariant,
    Color,
    Size
)
from .services import CatalogueArchiveService

archive_service = CatalogueArchiveService()


def archive_selected_products(modeladmin, request, queryset):
    for product in queryset:
        archive_service.archive_product(product)


def reactivate_selected_products(modeladmin, request, queryset):
    for product in queryset:
        archive_service.reactivate_product(product)


def archive_selected_categories(modeladmin, request, queryset):
    for category in queryset:
        archive_service.archive_category(category)


def reactivate_selected_categories(modeladmin, request, queryset):
    for category in queryset:
        archive_service.reactivate_category(category)


# =========================
# MEDIA INLINE
# =========================
class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ('media_type', 'file', 'order')
    ordering = ('order',)
    readonly_fields = ('format', 'mime_type', 'size_bytes', 'width', 'height', 'duration_seconds', 'checksum')
    can_delete = False


class ProductMediaAdminForm(forms.ModelForm):
    class Meta:
        model = ProductMedia
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        product, media_type = cleaned.get("product"), cleaned.get("media_type")
        if product and media_type and not self.instance.pk:
            maximum = settings.MAX_PRODUCT_IMAGES if media_type == "image" else settings.MAX_PRODUCT_VIDEOS
            if product.media_files.filter(media_type=media_type, is_active=True).count() >= maximum:
                raise forms.ValidationError("media_quota_exceeded")
        return cleaned


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    form = ProductMediaAdminForm
    list_display = ("id", "product", "media_type", "format", "size_bytes", "width", "height", "duration_seconds", "is_active", "created_at")
    readonly_fields = ("format", "mime_type", "size_bytes", "width", "height", "duration_seconds", "checksum", "created_at")
    list_filter = ("media_type", "format", "is_active")
    list_select_related = ("product",)

    def has_delete_permission(self, request, obj=None):
        return False


# =========================
# VARIANT INLINE (COULEUR + TAILLE)
# =========================
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('color', 'size', 'stock', 'is_active')
    can_delete = False


# =========================
# CATEGORY ADMIN
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'date_created')
    list_filter = ('is_active',)
    actions = [archive_selected_categories, reactivate_selected_categories]
    search_fields = ('name',)
    ordering = ('-date_created',)

    def has_delete_permission(self, request, obj=None):
        return False


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
# COLLECTION PRODUCT INLINE
# =========================
class CollectionProductInline(admin.TabularInline):
    model = Product.collections.through
    extra = 1
    verbose_name = "Produit"
    verbose_name_plural = "Produits dans la collection"


class CollectionAdminForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        cover_type = cleaned_data.get('cover_type') or Collection.COVER_TYPE_IMAGE
        image = cleaned_data.get('image')
        video = cleaned_data.get('video')

        if cover_type == Collection.COVER_TYPE_IMAGE:
            cleaned_data['video'] = None

            if not image:
                self.add_error('image', "Upload an image when cover type is set to image.")

        if cover_type == Collection.COVER_TYPE_VIDEO:
            cleaned_data['image'] = None

            if not video:
                self.add_error('video', "Upload a video when cover type is set to video.")

        return cleaned_data

# =========================
# COLLECTION ADMIN
# =========================
@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    form = CollectionAdminForm
    list_display = ('name', 'cover_type', 'is_active', 'product_count', 'add_product_button')
    search_fields = ('name',)
    list_filter = ('is_active',)
    ordering = ('-created_at',)
    
    inlines = [CollectionProductInline]
    exclude = ('products',)  # Exclure le champ ManyToMany direct car on utilise l'inline
    fields = (
        'name',
        'slug',
        'description',
        'cover_type',
        'image',
        'video',
        'is_active',
        'start_date',
        'end_date',
    )

    def product_count(self, obj):
        """Affiche le nombre de produits dans cette collection"""
        count = obj.products.count()
        return f"{count} produit{'s' if count != 1 else ''}"
    product_count.short_description = "Produits"

    def add_product_button(self, obj):
        """Bouton pour ajouter un produit à cette collection"""
        url = f'/admin/products/product/add/?collection={obj.id}'
        return format_html('<a class="addlink" href="{}">Ajouter un produit</a>', url)
    add_product_button.short_description = "Actions"
    add_product_button.allow_tags = True

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
        'is_active',
        'date_created'
    )

    list_filter = ('category', 'is_active', 'date_created')
    list_select_related = ('category',)
    search_fields = ('name', 'description')
    ordering = ('-date_created',)
    readonly_fields = ('date_created',)
    actions = [archive_selected_products, reactivate_selected_products]

    inlines = [
        ProductVariantInline
    ]

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'category', 'description')  # 🔥 AJOUT
        }),
        ('Prix & ventes', {
            'fields': ('price', 'sales_count', 'is_active')
        }),
        ('Système', {
            'fields': ('date_created',),
            'classes': ('collapse',)
        }),
    )

    def get_changeform_initial_data(self, request):
        """Pré-remplir le champ collections si un paramètre collection est passé"""
        initial = super().get_changeform_initial_data(request)
        collection_id = request.GET.get('collection')
        if collection_id:
            try:
                collection_id = int(collection_id)
                initial['collections'] = [collection_id]
            except (ValueError, TypeError):
                pass
        return initial

    def has_delete_permission(self, request, obj=None):
        return False

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
