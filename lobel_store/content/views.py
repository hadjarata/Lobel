from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import CustomDressService, HomeHero
from content.serializers import CustomDressServiceSerializer, HomeHeroSerializer


class HomeHeroView(APIView):
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(
        operation_summary="Couverture publiée de la page d'accueil",
        responses={
            200: HomeHeroSerializer,
            204: openapi.Response("Aucune couverture actuellement publiée."),
        },
    )
    def get(self, request):
        hero = HomeHero.objects.first()
        if hero is None:
            response = Response(status=status.HTTP_204_NO_CONTENT)
        else:
            response = Response(
                HomeHeroSerializer(hero, context={"request": request}).data
            )
        response["Cache-Control"] = "public, max-age=60"
        return response


class CustomDressServiceView(APIView):
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(
        operation_summary="Service actif de confection de robe sur mesure",
        responses={
            200: CustomDressServiceSerializer,
            204: openapi.Response("Aucun service actuellement actif."),
        },
    )
    def get(self, request):
        service = CustomDressService.objects.filter(is_active=True).first()
        response = (
            Response(
                CustomDressServiceSerializer(
                    service, context={"request": request}
                ).data
            )
            if service
            else Response(status=status.HTTP_204_NO_CONTENT)
        )
        response["Cache-Control"] = "public, max-age=60"
        return response
