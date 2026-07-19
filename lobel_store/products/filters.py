from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend


class ProductQueryFilter(BaseFilterBackend):
    ordering_fields = {"name", "price", "date_created", "sales_count"}

    def _decimal(self, request, name):
        raw = request.query_params.get(name)
        if raw in (None, ""):
            return None
        try:
            return Decimal(raw)
        except InvalidOperation as exc:
            raise ValidationError({name: "Un nombre valide est requis."}) from exc

    def filter_queryset(self, request, queryset, view):
        params = request.query_params
        search = params.get("search", "").strip()
        if len(search) > view.max_search_length:
            raise ValidationError({"search": "Terme de recherche trop long."})
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(category__name__icontains=search)
                | Q(collections__name__icontains=search)
                | Q(variants__sku__icontains=search)
            ).distinct()
        category = params.get("category")
        if category:
            if not category.isdigit():
                raise ValidationError({"category": "Un identifiant entier est requis."})
            queryset = queryset.filter(category_id=int(category))
        collection = params.get("collection")
        if collection:
            queryset = (
                queryset.filter(collections_id=int(collection))
                if collection.isdigit()
                else queryset.filter(collections__slug=collection)
            )
        minimum, maximum = self._decimal(request, "min_price"), self._decimal(request, "max_price")
        if minimum is not None and minimum < 0 or maximum is not None and maximum < 0:
            raise ValidationError({"price": "Le prix doit être positif."})
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValidationError({"price": "Intervalle de prix incohérent."})
        if minimum is not None:
            queryset = queryset.filter(price__gte=minimum)
        if maximum is not None:
            queryset = queryset.filter(price__lte=maximum)
        available = params.get("available")
        if available:
            if available.lower() not in {"true", "false", "1", "0"}:
                raise ValidationError({"available": "Utiliser true ou false."})
            queryset = queryset.filter(is_available=available.lower() in {"true", "1"})
        color, size = params.get("color"), params.get("size")
        if color:
            if not color.isdigit():
                raise ValidationError({"color": "Un identifiant entier est requis."})
            queryset = queryset.filter(variants__color_id=int(color), variants__is_active=True)
        if size:
            if not size.isdigit():
                raise ValidationError({"size": "Un identifiant entier est requis."})
            queryset = queryset.filter(variants__size_id=int(size), variants__is_active=True)
        ordering = params.get("ordering") or (
            "-sales_count" if getattr(view, "action", "") == "bestsellers" else "-date_created"
        )
        requested = [field for field in ordering.split(",") if field]
        if any(field.lstrip("-") not in self.ordering_fields for field in requested):
            raise ValidationError({"ordering": "Champ de tri non autorisé."})
        return queryset.distinct().order_by(*requested, "-id")

    def get_schema_operation_parameters(self, view):
        return [
            {"name": "search", "required": False, "in": "query", "description": "Nom, catégorie, collection ou SKU.", "schema": {"type": "string"}},
            {"name": "category", "required": False, "in": "query", "description": "Identifiant de catégorie.", "schema": {"type": "integer"}},
            {"name": "collection", "required": False, "in": "query", "description": "Identifiant ou slug de collection.", "schema": {"type": "string"}},
            {"name": "available", "required": False, "in": "query", "description": "true si une variante active est en stock.", "schema": {"type": "boolean"}},
            {"name": "min_price", "required": False, "in": "query", "schema": {"type": "number"}},
            {"name": "max_price", "required": False, "in": "query", "schema": {"type": "number"}},
            {"name": "color", "required": False, "in": "query", "schema": {"type": "integer"}},
            {"name": "size", "required": False, "in": "query", "schema": {"type": "integer"}},
            {"name": "ordering", "required": False, "in": "query", "description": "name, price, date_created ou sales_count; préfixe - pour décroissant.", "schema": {"type": "string"}},
        ]
