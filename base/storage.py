from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class StaticStorage(S3Boto3Storage):
    location = 'public/static'
    default_acl = 'public-read'
    file_overwrite = True
    querystring_auth = False
    
    def _normalize_name(self, name):
        if name.startswith('/'):
            name = name[1:]
        return name

class PublicMediaStorage(S3Boto3Storage):
    location = 'public'
    file_overwrite = False
    querystring_auth = False
    
    def __init__(self, custom_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = 'public/' + (custom_path + '/' if custom_path else '')

    def _normalize_name(self, name):
        name = name.replace('//', '/')
        
        if 'reports/reports' in name:
            name = name.replace('reports/reports', 'reports')
            
        if name.startswith(f"{self.location}/"):
            name = name[len(self.location)+1:]
            
        return super()._normalize_name(name)

class PrivateMediaStorage(S3Boto3Storage):
    location = 'private'
    file_overwrite = False
    
    def __init__(self, custom_path=None, **kwargs):
        self._custom_path = custom_path
        super().__init__(**kwargs)
    
    def _normalize_name(self, name):
        if name.startswith('/'):
            name = name[1:]
        
        if self._custom_path and not name.startswith(self._custom_path):
            name = f"{self._custom_path}/{name}"
            
        return name