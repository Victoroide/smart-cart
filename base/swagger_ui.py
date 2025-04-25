from django.views.generic import TemplateView
from django.urls import path
from drf_spectacular.views import SpectacularAPIView

class CustomSwaggerUIView(TemplateView):
    template_name = 'swagger-ui.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schema_url = self.request.build_absolute_uri('/schema/')
        context['schema_url'] = schema_url
        return context

def get_swagger_urls():
    return [
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('docs/', CustomSwaggerUIView.as_view(), name='swagger-ui'),
    ]