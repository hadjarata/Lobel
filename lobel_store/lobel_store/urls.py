from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from users.views import LoginView, LogoutView, RefreshView

from django.conf import settings
from django.conf.urls.static import static

api_info = openapi.Info(
    title="Lobel Store API",
    default_version='v1',
    description="Documentation API pour Lobel Store",
)

schema_view = get_schema_view(
   api_info,
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path(f"{getattr(settings, 'ADMIN_PATH', 'admin').strip('/')}/", admin.site.urls),

    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', RefreshView.as_view(), name='token_refresh'),
    path('api/auth/login/', LoginView.as_view(), name='auth_login'),
    path('api/auth/refresh/', RefreshView.as_view(), name='auth_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),

    # APIs
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),

]
if getattr(settings, "ENABLE_API_DOCS", False):
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
