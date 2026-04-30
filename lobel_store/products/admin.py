from django import forms
from django.contrib import admin, messages
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
        'date_created'
    )

    list_filter = ('category', 'date_created')
    search_fields = ('name', 'description')
    ordering = ('-date_created',)
    readonly_fields = ('date_created',)

    inlines = [
        ProductMediaInline,
        ProductVariantInline
    ]

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'category', 'description')  # 🔥 AJOUT
        }),
        ('Prix & ventes', {
            'fields': ('price', 'sales_count')
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
