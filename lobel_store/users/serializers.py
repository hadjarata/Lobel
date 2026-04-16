from rest_framework import serializers
from .models import Customer
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # nested serializer pour inclure les infos User

    class Meta:
        model = Customer
        fields = ['id', 'user', 'phone', 'address', 'date_created']