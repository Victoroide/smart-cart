from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'


class PublicMediaStorage(S3Boto3Storage):
    location = 'public'
    default_acl = 'public-read'
    file_overwrite = False

    def __init__(self, custom_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if custom_path:
            self.location = 'public/' + custom_path + '/'


class PrivateMediaStorage(S3Boto3Storage):
    location = 'private'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False

    def __init__(self, custom_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if custom_path:
            self.location = 'private/' + custom_path + '/'
