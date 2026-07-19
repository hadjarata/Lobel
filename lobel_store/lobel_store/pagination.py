from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from django.conf import settings


class StandardResultsSetPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def __init__(self):
        super().__init__()
        self.page_size = settings.API_DEFAULT_PAGE_SIZE
        self.max_page_size = settings.API_MAX_PAGE_SIZE

    def get_page_size(self, request):
        raw = request.query_params.get(self.page_size_query_param)
        if raw is None:
            return self.page_size
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"page_size": "Un entier positif est requis."}) from exc
        if value <= 0:
            raise ValidationError({"page_size": "La taille doit être positive."})
        return min(value, self.max_page_size)
