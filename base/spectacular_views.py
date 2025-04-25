import os
import mimetypes
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.urls import path
from drf_spectacular.views import SpectacularAPIView
from pathlib import Path
import requests

class SwaggerUIView(TemplateView):
    template_name = 'swagger-ui.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schema_url'] = self.request.build_absolute_uri('/schema/')
        return context

def serve_swagger_file(request, filename):
    print(f"Looking for swagger file: {filename}")
    
    # Define the content directly in the code for critical files
    if filename == 'swagger-ui.css':
        with open('staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui.css', 'wb') as f:
            f.write(requests.get('https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css').content)
        return HttpResponse(open('staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui.css', 'rb').read(), content_type='text/css')
    
    elif filename == 'swagger-ui-bundle.js':
        with open('staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js', 'wb') as f:
            f.write(requests.get('https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js').content)
        return HttpResponse(open('staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js', 'rb').read(), content_type='application/javascript')
    
    elif filename == 'swagger-ui-standalone-preset.js':
        with open('staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-standalone-preset.js', 'wb') as f:
            f.write(requests.get('https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js').content)
        return HttpResponse(open('staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-standalone-preset.js', 'rb').read(), content_type='application/javascript')
    
    else:
        return HttpResponse(f"File not found: {filename}", status=404)

def get_spectacular_urls():
    import requests  # Import here to avoid issues at module level
    
    return [
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('docs/', SwaggerUIView.as_view(), name='swagger-ui'),
        
        path('swagger-ui-assets/swagger-ui.css', serve_swagger_file, {'filename': 'swagger-ui.css'}),
        path('swagger-ui-assets/swagger-ui-bundle.js', serve_swagger_file, {'filename': 'swagger-ui-bundle.js'}),
        path('swagger-ui-assets/swagger-ui-standalone-preset.js', serve_swagger_file, {'filename': 'swagger-ui-standalone-preset.js'}),
    ]