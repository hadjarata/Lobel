from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Customer
from .validators import normalize_phone_number, validate_country_code


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active']


class CustomerReadSerializer(serializers.ModelSerializer):
    """Lecture seule – list, retrieve, me."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'user',
            'country',
            'phone_number',
            'address',
            'date_created',
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Inscription uniquement – POST /api/users/customers/."""

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(write_only=True, allow_blank=True, required=False)
    last_name = serializers.CharField(write_only=True, allow_blank=True, required=False)

    class Meta:
        model = Customer
        fields = [
            'email',
            'password',
            'first_name',
            'last_name',
            'country',
            'phone_number',
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value

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
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )

        return Customer.objects.create(user=user, **validated_data)


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour profil – PATCH /api/users/customers/{id}/."""

    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = [
            'first_name',
            'last_name',
            'country',
            'phone_number',
            'address',
        ]

    def validate_country(self, value):
        try:
            return validate_country_code(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_phone_number(self, value):
        if not value:
            return ''
        try:
            return normalize_phone_number(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def update(self, instance, validated_data):
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)

        user = instance.user
        user_fields = []

        if first_name is not None:
            user.first_name = first_name.strip()
            user_fields.append('first_name')
        if last_name is not None:
            user.last_name = last_name.strip()
            user_fields.append('last_name')

        if user_fields:
            user.save(update_fields=user_fields)

        return super().update(instance, validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        if len(data['password']) < 6:
            raise serializers.ValidationError("Le mot de passe doit contenir au moins 6 caractères.")
        return data


class VerifyEmailSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


# Alias rétrocompatibilité
CustomerSerializer = CustomerReadSerializer
EmailVerificationSerializer = VerifyEmailSerializer
