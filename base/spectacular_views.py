import os
import mimetypes
from django.http import HttpResponse, FileResponse
from django.views.generic import TemplateView
from django.urls import path
from drf_spectacular.views import SpectacularAPIView
from django.conf import settings

class SwaggerUIView(TemplateView):
    template_name = 'swagger-ui.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schema_url'] = self.request.build_absolute_uri('/schema/')
        return context

def serve_swagger_file(request, filename):
    base_dir = os.path.join(settings.BASE_DIR, 'staticfiles', 'drf_spectacular_sidecar', 'swagger-ui-dist')
    file_path = os.path.join(base_dir, filename)
    
    content_type, encoding = mimetypes.guess_type(file_path)
    content_type = content_type or 'application/octet-stream'
    
    try:
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        if encoding:
            response['Content-Encoding'] = encoding
        return response
    except FileNotFoundError:
        return HttpResponse(f"File {filename} not found", status=404)

def get_spectacular_urls():
    return [
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('docs/', SwaggerUIView.as_view(), name='swagger-ui'),
        
        path('swagger-ui-assets/swagger-ui.css', serve_swagger_file, {'filename': 'swagger-ui.css'}),
        path('swagger-ui-assets/swagger-ui-bundle.js', serve_swagger_file, {'filename': 'swagger-ui-bundle.js'}),
        path('swagger-ui-assets/swagger-ui-standalone-preset.js', serve_swagger_file, {'filename': 'swagger-ui-standalone-preset.js'}),
        path('swagger-ui-assets/favicon-32x32.png', serve_swagger_file, {'filename': 'favicon-32x32.png'}),
    ]