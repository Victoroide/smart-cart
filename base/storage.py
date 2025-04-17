from storages.backends.s3boto3 import S3Boto3Storage
from base import settings

class StaticStorage(S3Boto3Storage):
    location = 'public/static'
    file_overwrite = True

class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = 'public'
    file_overwrite = False

    def __init__(self, custom_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = 'public/' + (custom_path + '/' if custom_path else '')

class PrivateMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = 'private'
    file_overwrite = False
    custom_domain = False

    def __init__(self, custom_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = 'private/' + (custom_path + '/' if custom_path else '')