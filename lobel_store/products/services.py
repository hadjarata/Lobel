from django.db import transaction

from .models import Category, Product, ProductVariant


class CatalogueArchiveService:
    @transaction.atomic
    def archive_product(self, product):
        product = Product.objects.select_for_update().get(pk=product.pk)
        product.is_active = False
        product.save(update_fields=["is_active"])
        ProductVariant.objects.filter(product=product).update(is_active=False)
        return product

    @transaction.atomic
    def reactivate_product(self, product):
        product = Product.objects.select_for_update().select_related("category").get(
            pk=product.pk
        )
        if not product.category.is_active:
            raise ValueError("La catégorie doit être active.")
        product.is_active = True
        product.save(update_fields=["is_active"])
        return product

    @transaction.atomic
    def archive_category(self, category):
        category = Category.objects.select_for_update().get(pk=category.pk)
        category.is_active = False
        category.save(update_fields=["is_active"])
        return category

    @transaction.atomic
    def reactivate_category(self, category):
        category = Category.objects.select_for_update().get(pk=category.pk)
        category.is_active = True
        category.save(update_fields=["is_active"])
        return category

    @transaction.atomic
    def archive_variant(self, variant):
        variant = ProductVariant.objects.select_for_update().get(pk=variant.pk)
        variant.is_active = False
        variant.save(update_fields=["is_active"])
        return variant
