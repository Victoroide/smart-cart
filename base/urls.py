from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from base import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
   openapi.Info(
      title="Smart Cart API",
      default_version='v1',
      description="Documentación completa de la API de Smart Cart",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="soporte@smartcart.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/core/', include('core.urls')),
    path('api/auth/', include('app.authentication.urls')),
    path('api/products/', include('app.products.urls')),
    path('api/orders/', include('app.orders.urls')),
    path('api/chatbot/', include('app.chatbot.urls')),
    path('api/reports/', include('app.reports.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

if settings.DEBUG:
    if not settings.USE_S3:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)