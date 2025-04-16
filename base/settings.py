from pathlib import Path
import os
from urllib.parse import urlparse
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-clec8vo#+c@mu&hjoo6lgr6_b8z4=(3f#*vo0j#&kbncfn)=()")
DEBUG = config("DEBUG", default="True") == "True"
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', 'localhost:4200', "localhost:5500"]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    BACKEND_URL := config("BACKEND_URL", default="http://localhost:8000"),
    FRONTEND_URL := config("FRONTEND_URL", default="http://localhost:4200"),
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
    'app.authentication',
    'app.products',
    'app.orders',
    'app.chatbot',
    'app.reports',
    'drf_yasg',
    'storages'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'base.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static'
            ],
        },
    },
]

WSGI_APPLICATION = 'base.wsgi.application'

tmpPostgres = urlparse(config("DATABASE_URL", default=""))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

USE_S3 = config('USE_S3', default='False') == 'True'

if USE_S3:
    # aws settings
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_DEFAULT_ACL = None
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_REGION_NAME = 'us-east-1'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_S3_FILE_OVERWRITE = True
    # s3 static settings
    STATIC_LOCATION = 'static'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
    STATICFILES_STORAGE = 'base.storage_backend.StaticStorage'
    # s3 public media settings
    PUBLIC_MEDIA_LOCATION = 'media'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
    DEFAULT_FILE_STORAGE = 'base.storage_backend.PublicMediaStorage'
    # s3 private media settings
    PRIVATE_MEDIA_LOCATION = 'private'
    PRIVATE_FILE_STORAGE = 'base.storage_backend.PrivateMediaStorage'
else:
    STATIC_URL = '/staticfiles/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_URL = '/mediafiles/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'authentication.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPagination',
    'PAGE_SIZE': 20,
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
    'VALIDATOR_URL': None,
}

PINECONE_INDEX_NAME = config('PINECONE_INDEX_NAME')
PINECONE_API_KEY = config('PINECONE_API_KEY')

OPENAI_AZURE_API_KEY = config('OPENAI_AZURE_API_KEY')
OPENAI_AZURE_API_BASE = config('OPENAI_AZURE_API_BASE')
OPENAI_AZURE_API_VERSION = config('OPENAI_AZURE_API_VERSION')
OPENAI_BASE_MODEL = config('OPENAI_BASE_MODEL')
OPENAI_THINKING_MODEL = config('OPENAI_THINKING_MODEL')
OPENAI_EMBEDDING_MODEL = config('OPENAI_EMBEDDING_MODEL')

USD_TO_BS_RATE = 13
STRIPE_API_KEY = config('STRIPE_API_KEY')
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET')

PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET')
PAYPAL_SANDBOX = config('PAYPAL_SANDBOX', default='True') == 'True'
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_SANDBOX else "https://api-m.paypal.com"

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:4200')