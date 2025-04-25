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
    location = 'public/media'
    file_overwrite = False
    querystring_auth = False
    
    def __init__(self, custom_path=None, **kwargs):
        self._custom_path = custom_path
        super().__init__(**kwargs)
    
    def _normalize_name(self, name):
        if name.startswith('/'):
            name = name[1:]
        
        if self._custom_path and not name.startswith(self._custom_path):
            name = f"{self._custom_path}/{name}"
            
        return name

class PrivateMediaStorage(S3Boto3Storage):
    location = 'private/media'
    default_acl = 'private'
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