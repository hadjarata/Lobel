from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Customer
from .serializers import (
    CustomerSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer,
    EmailVerificationSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.action in [
            'create',
            'request_password_reset',
            'reset_password',
            'verify_email'
        ]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self._send_verification_email(serializer.instance.user, request)
        return Response(
            {'detail': 'Votre compte a été créé. Vérifiez votre email pour activer le compte.'},
            status=status.HTTP_201_CREATED
        )

    def _build_frontend_link(self, request, path):
        base_url = getattr(settings, 'FRONTEND_URL', None)
        if base_url:
            return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        return request.build_absolute_uri(path)

    def _send_verification_email(self, user, request):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = self._build_frontend_link(request, f"verify-email?uid={uid}&token={token}")
        message = (
            f"Bonjour {user.first_name or user.username},\n\n"
            "Merci de vous être inscrit sur Lobel Store.\n"
            f"Cliquez sur le lien suivant pour vérifier votre adresse email :\n{verify_url}\n\n"
            "Si vous n'avez pas créé ce compte, ignorez ce message."
        )
        send_mail(
            'Vérification de l\'email Lobel Store',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

    def _send_password_reset_email(self, user, request):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = self._build_frontend_link(request, f"reset-password?uid={uid}&token={token}")
        message = (
            f"Bonjour {user.first_name or user.username},\n\n"
            "Vous avez demandé une réinitialisation de votre mot de passe.\n"
            f"Cliquez sur le lien suivant pour choisir un nouveau mot de passe :\n{reset_url}\n\n"
            "Si vous n'avez pas demandé cette réinitialisation, ignorez ce message."
        )
        send_mail(
            'Réinitialisation du mot de passe Lobel Store',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        user = request.user

        if not user or not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        customer = Customer.objects.filter(user=user).first()

        if not customer:
            return Response(
                {"detail": "Customer profile not found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(customer)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='request-password-reset', permission_classes=[permissions.AllowAny])
    def request_password_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email__iexact=email).first()
        if user:
            self._send_password_reset_email(user, request)

        return Response(
            {'detail': 'Si l\'email existe, un lien de réinitialisation a été envoyé.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='reset-password', permission_classes=[permissions.AllowAny])
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']

        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Lien de réinitialisation invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'Le lien de réinitialisation est invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(password)
        user.is_active = True
        user.save()

        return Response(
            {'detail': 'Le mot de passe a été réinitialisé avec succès.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='verify-email', permission_classes=[permissions.AllowAny])
    def verify_email(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']

        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Lien de vérification invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'Le lien de vérification est invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.save()

        return Response(
            {'detail': 'Email vérifié avec succès. Vous pouvez maintenant vous connecter.'},
            status=status.HTTP_200_OK
        )
