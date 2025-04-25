from storages.backends.s3boto3 import S3Boto3Storage
from django.contrib.staticfiles.storage import StaticFilesStorage

class StaticStorage(S3Boto3Storage):
    location = 'public/static'
    file_overwrite = True
    default_acl = 'public-read'
    
    def _save_content(self, obj, content, parameters):
        content_type = getattr(content, 'content_type', None)
        if content_type and 'ContentType' not in parameters:
            parameters['ContentType'] = content_type
        return super()._save_content(obj, content, parameters)

class SpectacularStaticStorage(StaticFilesStorage):
    location = 'staticfiles/drf_spectacular_sidecar'

class PublicMediaStorage(S3Boto3Storage):
    location = 'public'
    file_overwrite = False

    def __init__(self, custom_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = 'public/' + (custom_path + '/' if custom_path else '')

class PrivateMediaStorage(S3Boto3Storage):
    location = 'private'
    file_overwrite = False
    custom_domain = False

    def __init__(self, custom_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = 'private/' + (custom_path + '/' if custom_path else '')