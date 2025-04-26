from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .spectacular_views import get_spectacular_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('app.authentication.urls')),
    path('api/products/', include('app.products.urls')),
    path('api/orders/', include('app.orders.urls')),
    path('api/chatbot/', include('app.chatbot.urls')),
    path('api/reports/', include('app.reports.urls')),
    path('api/parameters/', include('app.parameter.urls')),
    path('api/core/', include('core.urls')),
]

urlpatterns = get_spectacular_urls() + urlpatterns

if settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)