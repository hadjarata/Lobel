from rest_framework import serializers

from content.models import CustomDressService, HomeHero


class HomeHeroSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = HomeHero
        fields = ("title", "description", "media_type", "media_url")

    def _url(self, field):
        if not field:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(field.url) if request else field.url

    def get_media_url(self, obj):
        field = obj.image if obj.media_type == HomeHero.MEDIA_IMAGE else obj.video
        return self._url(field)


class CustomDressServiceSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()

    class Meta:
        model = CustomDressService
        fields = (
            "title", "description", "image_url", "whatsapp_phone",
            "whatsapp_message", "button_label", "availability_text",
            "response_time_text", "pricing_notice", "steps",
        )

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

    def get_steps(self, obj):
        return [
            "Envoyez votre modèle ou votre inspiration",
            "Discutez du tissu, des mesures et des finitions",
            "Recevez une estimation du prix et du délai",
            "Validez la confection avec notre responsable",
        ]
