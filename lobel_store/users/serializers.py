from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Customer
from .services import can_authenticate_user, normalize_email
from .validators import normalize_phone_number, validate_country_code


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_active"]


class CustomerReadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "user", "country", "phone_number", "address", "date_created"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True, allow_blank=True, required=False)
    last_name = serializers.CharField(write_only=True, allow_blank=True, required=False)

    class Meta:
        model = Customer
        fields = ["email", "password", "first_name", "last_name", "country", "phone_number"]

    def validate_email(self, value):
        value = normalize_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return value

    def validate(self, attrs):
        candidate = User(
            username=attrs.get("email", ""),
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        try:
            validate_password(attrs["password"], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def validate_country(self, value):
        try:
            return validate_country_code(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_phone_number(self, value):
        if not value:
            return value
        try:
            return normalize_phone_number(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email, email=email, password=password,
                    first_name=first_name, last_name=last_name, is_active=True,
                )
                return Customer.objects.create(user=user, **validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"email": "Cette adresse e-mail est déjà utilisée."}
            ) from exc


class CustomerUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "country", "phone_number", "address"]

    def validate_country(self, value):
        try:
            return validate_country_code(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_phone_number(self, value):
        if not value:
            return ""
        try:
            return normalize_phone_number(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def update(self, instance, validated_data):
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        fields = []
        if first_name is not None:
            instance.user.first_name = first_name.strip()
            fields.append("first_name")
        if last_name is not None:
            instance.user.last_name = last_name.strip()
            fields.append("last_name")
        if fields:
            instance.user.save(update_fields=fields)
        return super().update(instance, validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data


class VerifyEmailSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = normalize_email(attrs.get(self.username_field, ""))
        user = authenticate(
            request=self.context.get("request"), username=identifier,
            password=attrs.get("password"),
        )
        if not can_authenticate_user(user):
            raise AuthenticationFailed("Identifiants invalides ou compte indisponible.")
        refresh = self.get_token(user)
        refresh["token_version"] = user.customer.token_version
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


class AccountTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = RefreshToken(attrs["refresh"])
        try:
            user = User.objects.select_related("customer").get(pk=token.get("user_id"))
        except User.DoesNotExist as exc:
            raise InvalidToken("Token invalide.") from exc
        if not can_authenticate_user(user) or token.get("token_version") != user.customer.token_version:
            raise AuthenticationFailed("Compte indisponible.")
        data = super().validate(attrs)
        if "refresh" in data:
            rotated = RefreshToken(data["refresh"])
            rotated["token_version"] = user.customer.token_version
            data["refresh"] = str(rotated)
            data["access"] = str(rotated.access_token)
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Mot de passe incorrect."})
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        try:
            validate_password(attrs["password"], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs


CustomerSerializer = CustomerReadSerializer
EmailVerificationSerializer = VerifyEmailSerializer
