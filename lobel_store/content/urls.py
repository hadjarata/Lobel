from django.urls import path

from content.views import CustomDressServiceView, HomeHeroView

urlpatterns = [
    path("home-hero/", HomeHeroView.as_view(), name="home-hero"),
    path(
        "custom-dress-service/",
        CustomDressServiceView.as_view(),
        name="custom-dress-service",
    ),
]
