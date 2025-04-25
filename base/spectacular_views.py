from drf_spectacular.views import SpectacularSwaggerView as BaseSpectacularSwaggerView
from drf_spectacular.views import SpectacularRedocView as BaseSpectacularRedocView
from django.conf import settings
from django.urls import re_path
import os

class SpectacularSwaggerView(BaseSpectacularSwaggerView):
    @property
    def urls(self):
        urls = super().urls
        
        # Force the static URLs to use the local path
        for i, url in enumerate(urls):
            if hasattr(url, 'pattern') and 'swagger-ui-dist' in str(url.pattern):
                path_parts = str(url.pattern).split('swagger-ui-dist/')
                if len(path_parts) > 1:
                    file_path = path_parts[1].replace("'", "").replace('"', '')
                    urls[i] = re_path(
                        r'^swagger-ui-dist/{}$'.format(file_path),
                        self.serve_file(
                            os.path.join(settings.BASE_DIR, 'staticfiles', 'drf_spectacular_sidecar', 'swagger-ui-dist', file_path)
                        ),
                        name=f'swagger-ui-dist-{file_path}'
                    )
        return urls

class SpectacularRedocView(BaseSpectacularRedocView):
    @property
    def urls(self):
        urls = super().urls
        
        # Force the static URLs to use the local path
        for i, url in enumerate(urls):
            if hasattr(url, 'pattern') and 'redoc/' in str(url.pattern):
                path_parts = str(url.pattern).split('redoc/')
                if len(path_parts) > 1:
                    file_path = path_parts[1].replace("'", "").replace('"', '')
                    urls[i] = re_path(
                        r'^redoc/{}$'.format(file_path),
                        self.serve_file(
                            os.path.join(settings.BASE_DIR, 'staticfiles', 'drf_spectacular_sidecar', 'redoc', file_path)
                        ),
                        name=f'redoc-{file_path}'
                    )
        return urls