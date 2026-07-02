from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=3, blank=True, help_text="Code pays ISO (ex: FR, ML)")  # ISO alpha-2
    phone_number = models.CharField(max_length=20, blank=True, help_text="Numéro de téléphone au format international")
    address = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username