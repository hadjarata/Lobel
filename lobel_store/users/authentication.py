from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .services import can_authenticate_user


class AccountJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not can_authenticate_user(user):
            raise AuthenticationFailed("Compte indisponible.", code="account_unavailable")
        if validated_token.get("token_version") != user.customer.token_version:
            raise AuthenticationFailed("Session révoquée.", code="session_revoked")
        return user
