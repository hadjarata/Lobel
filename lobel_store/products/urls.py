from rest_framework import routers
from .views import CategoryViewSet, ProductViewSet, CollectionViewSet

router = routers.DefaultRouter()

router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'collections', CollectionViewSet)  # 🔥 AJOUT IMPORTANT

urlpatterns = router.urls