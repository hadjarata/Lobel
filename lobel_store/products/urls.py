from rest_framework import routers
from .views import CategoryViewSet, ProductViewSet, CollectionViewSet, ProductMediaViewSet

router = routers.DefaultRouter()

router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'collections', CollectionViewSet)  # 🔥 AJOUT IMPORTANT

router.register(r'media', ProductMediaViewSet)

urlpatterns = router.urls
