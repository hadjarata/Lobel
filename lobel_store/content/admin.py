from django import forms
from django.conf import settings
from django.contrib import admin

from content.models import CustomDressService, HomeHero


class HomeHeroAdminForm(forms.ModelForm):
    class Meta:
        model = HomeHero
        fields = ("title", "description", "media_type", "image", "video")
        help_texts = {
            "image": (
                f"JPEG, PNG ou WebP, "
                f"{settings.HOME_HERO_MAX_IMAGE_SIZE_MB} Mo maximum."
            ),
            "video": (
                f"Vidéo courte et compressée, MP4 H.264, "
                f"{settings.HOME_HERO_MAX_VIDEO_SIZE_MB} Mo maximum."
            ),
        }


@admin.register(HomeHero)
class HomeHeroAdmin(admin.ModelAdmin):
    form = HomeHeroAdminForm
    list_display = ("title", "media_type")
    list_filter = ("media_type",)
    search_fields = ("title",)
    fieldsets = (
        ("Contenu", {"fields": ("title", "description")}),
        (
            "Média",
            {"fields": ("media_type", "image", "video")},
        ),
    )

    def has_add_permission(self, request):
        return not HomeHero.objects.exists() and super().has_add_permission(request)


class CustomDressServiceAdminForm(forms.ModelForm):
    class Meta:
        model = CustomDressService
        fields = "__all__"
        help_texts = {
            "image": (
                f"JPEG, PNG ou WebP, "
                f"{settings.CUSTOM_DRESS_MAX_IMAGE_SIZE_MB} Mo maximum."
            ),
            "whatsapp_phone": (
                "8 à 15 chiffres, indicatif pays inclus. Aucun +, espace, tiret "
                "ou lien wa.me."
            ),
            "whatsapp_message": (
                "Message prérempli générique. N'ajoutez aucune donnée personnelle."
            ),
            "is_active": (
                "Une seule configuration peut être active ; l'ancienne sera désactivée."
            ),
        }


@admin.register(CustomDressService)
class CustomDressServiceAdmin(admin.ModelAdmin):
    form = CustomDressServiceAdminForm
    list_display = ("title", "masked_phone", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Contenu", {"fields": ("title", "description", "button_label")}),
        ("Image", {"fields": ("image",)}),
        ("Contact WhatsApp", {"fields": ("whatsapp_phone", "whatsapp_message")}),
        (
            "Informations pratiques",
            {"fields": ("availability_text", "response_time_text", "pricing_notice")},
        ),
        ("Publication", {"fields": ("is_active", "created_at", "updated_at")}),
    )

    @admin.display(description="Numéro WhatsApp")
    def masked_phone(self, obj):
        return f"{obj.whatsapp_phone[:3]}••••{obj.whatsapp_phone[-3:]}"
