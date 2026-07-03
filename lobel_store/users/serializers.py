from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer

import phonenumbers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active']


class CustomerSerializer(serializers.ModelSerializer):
    # champs pour création user
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)

    # affichage user
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'user',
            'email',
            'password',
            'first_name',
            'last_name',
            'country',
            'phone_number',
            'address',
            'date_created',
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value

    def validate_country(self, value):
        if not value:
            return value
        value = value.strip().upper()
        valid_regions = {
            region for regions in phonenumbers.COUNTRY_CODE_TO_REGION_CODE.values() for region in regions
        }
        if value not in valid_regions:
            raise serializers.ValidationError("Le code pays est invalide.")
        return value

    def validate_phone_number(self, value):
        if not value:
            return value
        value = value.strip()
        if not value.startswith('+'):
            value = '+' + value
        try:
            phone = phonenumbers.parse(value, None)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Numéro de téléphone invalide.")
        if not phonenumbers.is_valid_number(phone):
            raise serializers.ValidationError("Numéro de téléphone invalide.")
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)

    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )

        customer = Customer.objects.create(user=user, **validated_data)

        return customer

    def update(self, instance, validated_data):
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)

        user = instance.user
        user_updated = False

        if first_name is not None:
            user.first_name = first_name
            user_updated = True
        if last_name is not None:
            user.last_name = last_name
            user_updated = True

        if user_updated:
            user.save(update_fields=['first_name', 'last_name'])

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


class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()