from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from .models import Category, Product, ProductMedia


class ProductMediaInline(admin.TabularInline):
    """Inline pour gérer les médias dans la page produit"""
    model = ProductMedia
    extra = 1
    min_num = 1  # Au moins un média requis
    fields = ('media_type', 'file', 'order')
    ordering = ('order',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_created')
    search_fields = ('name',)
    ordering = ('-date_created',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'sales_count', 'date_created')
    list_filter = ('category', 'date_created')
    search_fields = ('name', 'description')
    ordering = ('-date_created',)
    readonly_fields = ('date_created',)
    inlines = [ProductMediaInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'category', 'description')
        }),
        ('Prix et stock', {
            'fields': ('price', 'stock', 'sales_count')
        }),
        ('Informations système', {
            'fields': ('date_created',),
            'classes': ('collapse',)
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        """Valider qu'il y a au moins un média"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, ProductMedia):
                # Compter les médias existants (y compris ceux qui ne sont pas modifiés)
                if change:
                    total_media = ProductMedia.objects.filter(product=instance.product).count()
                    if total_media == 0 and not instance.file:
                        messages.error(request, "Un produit doit avoir au moins un média (image ou vidéo).")
                        raise ValidationError("Un produit doit avoir au moins un média.")
                elif not change and not instance.file:
                    messages.error(request, "Un produit doit avoir au moins un média (image ou vidéo).")
                    raise ValidationError("Un produit doit avoir au moins un média.")
        
        return super().save_formset(request, form, formset, change)
    
    def response_add(self, request, obj, post_url_continue=None):
        """Vérifier après l'ajout qu'il y a des médias"""
        if obj.media_files.count() == 0:
            messages.warning(request, "Attention : Ce produit n'a aucun média. Ajoutez au moins une image ou vidéo.")
        return super().response_add(request, obj, post_url_continue)
    
    def response_change(self, request, obj):
        """Vérifier après la modification qu'il y a des médias"""
        if obj.media_files.count() == 0:
            messages.warning(request, "Attention : Ce produit n'a aucun média. Ajoutez au moins une image ou vidéo.")
        return super().response_change(request, obj)