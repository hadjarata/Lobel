from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django import forms

# Register your models here.
from .models import Customer
from .services import normalize_email, revoke_user_tokens, suspend_user, unsuspend_user


class SecureUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = normalize_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email


class SecureUserChangeForm(UserChangeForm):
    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email", ""))
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email


class SecureUserAdmin(UserAdmin):
    add_form = SecureUserCreationForm
    form = SecureUserChangeForm


admin.site.unregister(User)
admin.site.register(User, SecureUserAdmin)


@admin.action(description="Suspendre les comptes sélectionnés")
def suspend_selected(modeladmin, request, queryset):
    for customer in queryset.select_related("user"):
        suspend_user(customer.user, reason="Suspension depuis l’administration")


@admin.action(description="Réactiver administrativement les comptes sélectionnés")
def unsuspend_selected(modeladmin, request, queryset):
    for customer in queryset.select_related("user"):
        unsuspend_user(customer.user)


@admin.action(description="Révoquer toutes les sessions")
def revoke_sessions(modeladmin, request, queryset):
    for customer in queryset.select_related("user"):
        revoke_user_tokens(customer.user)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "email_verified_at", "suspended_at", "country", "date_created")
    readonly_fields = ("email_verified_at", "suspended_at", "token_version", "date_created")
    actions = [suspend_selected, unsuspend_selected, revoke_sessions]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
