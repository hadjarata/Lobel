import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Customer
from .serializers import (
    AccountTokenRefreshSerializer, CustomerReadSerializer, CustomerUpdateSerializer,
    EmailTokenObtainPairSerializer, LogoutSerializer, PasswordChangeSerializer,
    PasswordResetRequestSerializer, PasswordResetSerializer, RegisterSerializer,
    VerifyEmailSerializer,
)
from .services import normalize_email, revoke_user_tokens
from .throttles import EmailRateThrottle

logger = logging.getLogger(__name__)


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class RefreshView(TokenRefreshView):
    serializer_class = AccountTokenRefreshSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token_refresh"


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "logout"

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            pass
        logger.info("auth.logout")
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("user")
    serializer_class = CustomerReadSerializer
    throttle_scope = None
    http_method_names = ["get", "post", "patch", "put", "head", "options"]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "register"
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "create":
            return RegisterSerializer
        if self.action in ("update", "partial_update"):
            return CustomerUpdateSerializer
        return CustomerReadSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Customer.objects.none()
        return self.queryset.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ("create", "request_password_reset", "reset_password", "verify_email"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self._send_verification_email(serializer.instance.user)
        return Response(
            {"detail": "Votre compte a été créé. Vérifiez votre e-mail."},
            status=status.HTTP_201_CREATED,
        )

    def _frontend_link(self, setting_name, fallback_path, uid, token):
        base = getattr(settings, setting_name, "") or f"{settings.FRONTEND_URL.rstrip('/')}/{fallback_path}"
        separator = "&" if "?" in base else "?"
        return f"{base}{separator}uid={uid}&token={token}"

    def _send_verification_email(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        url = self._frontend_link("FRONTEND_EMAIL_ACTIVATION_URL", "verify-email", uid, token)
        send_mail("Vérification de l'e-mail Lobel Store", f"Vérifiez votre adresse :\n{url}",
                  settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)

    def _send_password_reset_email(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        url = self._frontend_link("FRONTEND_RESET_PASSWORD_URL", "reset-password", uid, token)
        send_mail("Réinitialisation du mot de passe Lobel Store",
                  f"Choisissez un nouveau mot de passe :\n{url}",
                  settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            return Response({"detail": "Profil client introuvable."}, status=404)
        return Response(CustomerReadSerializer(customer).data)

    @action(
        detail=False, methods=["post"], url_path="request-password-reset",
        permission_classes=[permissions.AllowAny],
        throttle_classes=[ScopedRateThrottle, EmailRateThrottle],
        throttle_scope="password_reset_request",
    )
    def request_password_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.select_related("customer").filter(
            email__iexact=normalize_email(serializer.validated_data["email"])
        ).first()
        if (
            user and user.is_active and hasattr(user, "customer")
            and user.customer.email_verified_at and not user.customer.is_suspended
        ):
            self._send_password_reset_email(user)
        logger.info("auth.password_reset_requested")
        return Response(
            {"detail": "Si un compte correspondant existe, un message de réinitialisation sera envoyé."}
        )

    @action(
        detail=False, methods=["post"], url_path="reset-password",
        permission_classes=[permissions.AllowAny],
        throttle_classes=[ScopedRateThrottle], throttle_scope="password_reset_confirm",
    )
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.select_related("customer").get(
                pk=force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Lien de réinitialisation invalide."}, status=400)
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response({"detail": "Lien de réinitialisation invalide ou expiré."}, status=400)
        try:
            validate_password(serializer.validated_data["password"], user)
        except DjangoValidationError as exc:
            return Response({"password": list(exc.messages)}, status=400)
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        revoke_user_tokens(user)
        logger.info("auth.password_reset_confirmed user_id=%s", user.pk)
        return Response({"detail": "Mot de passe réinitialisé."})

    @action(
        detail=False, methods=["post"], url_path="verify-email",
        permission_classes=[permissions.AllowAny],
        throttle_classes=[ScopedRateThrottle], throttle_scope="email_activation",
    )
    def verify_email(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.select_related("customer").get(
                pk=force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Lien de vérification invalide."}, status=400)
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response({"detail": "Lien de vérification invalide ou expiré."}, status=400)
        if not user.customer.email_verified_at:
            user.customer.email_verified_at = timezone.now()
            user.customer.save(update_fields=["email_verified_at"])
        logger.info("auth.email_verified user_id=%s", user.pk)
        return Response({"detail": "E-mail vérifié."})

    @action(
        detail=False, methods=["post"], url_path="change-password",
        throttle_classes=[ScopedRateThrottle], throttle_scope="password_change",
    )
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["password"])
        request.user.save(update_fields=["password"])
        revoke_user_tokens(request.user)
        return Response({"detail": "Mot de passe modifié."})
