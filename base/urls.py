from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('app.authentication.urls')),
    path('api/products/', include('app.products.urls')),
    path('api/orders/', include('app.orders.urls')),
    path('api/chatbot/', include('app.chatbot.urls')),
    path('api/reports/', include('app.reports.urls')),
    path('api/core/', include('core.urls')),
    
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns += [
    path('static/drf_spectacular_sidecar/<path:path>', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'staticfiles', 'drf_spectacular_sidecar'),
    }),
]

if settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)