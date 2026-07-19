from django.conf import settings
from django.db import models

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    country = models.CharField(max_length=3, blank=True, help_text="Code pays ISO (ex: FR, ML)")  # ISO alpha-2
    phone_number = models.CharField(max_length=20, blank=True, help_text="Numéro de téléphone au format international")
    address = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.CharField(max_length=255, blank=True)
    token_version = models.PositiveIntegerField(default=0)

    @property
    def is_suspended(self):
        return self.suspended_at is not None

    def __str__(self):
        return self.user.username
