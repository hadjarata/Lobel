from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from .pagination import StandardResultsSetPagination


class APIConfigurationTests(SimpleTestCase):
    def test_safe_pagination_defaults(self):
        paginator = StandardResultsSetPagination()
        self.assertGreater(paginator.page_size, 0)
        self.assertGreaterEqual(paginator.max_page_size, paginator.page_size)

    def test_page_size_validation(self):
        paginator = StandardResultsSetPagination()
        request = APIRequestFactory().get("/", {"page_size": "abc"})
        from rest_framework.request import Request
        with self.assertRaises(Exception):
            paginator.get_page_size(Request(request))
