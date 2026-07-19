from rest_framework.throttling import SimpleRateThrottle

from .services import normalize_email


class EmailRateThrottle(SimpleRateThrottle):
    scope = "password_reset_request_email"

    def get_cache_key(self, request, view):
        email = normalize_email(request.data.get("email", "")).casefold()
        return self.cache_format % {"scope": self.scope, "ident": email} if email else None
