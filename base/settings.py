from pathlib import Path
import os
from urllib.parse import urlparse
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-clec8vo#+c@mu&hjoo6lgr6_b8z4=(3f#*vo0j#&kbncfn)=()")
DEBUG = config("DEBUG", default="True") == "True"
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', 'localhost:4200', "localhost:5500"]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    config("BACKEND_URL", default="http://localhost:8000"),
    config("FRONTEND_URL", default="http://localhost:4200"),
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
    'drf_spectacular',
    'drf_spectacular_sidecar',
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
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

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

if USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False
    
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/public/static/'
    STATICFILES_STORAGE = 'base.storage.StaticStorage'
    
    SPECTACULAR_STATIC_DIRNAME = os.path.join(STATIC_ROOT, 'drf_spectacular_sidecar')
    os.makedirs(SPECTACULAR_STATIC_DIRNAME, exist_ok=True)
    
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/public/media/'
    DEFAULT_FILE_STORAGE = 'base.storage.PublicMediaStorage'
    PRIVATE_FILE_STORAGE = 'base.storage.PrivateMediaStorage'
else:
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

STATIC_URL = '/static/' if not USE_S3 else f'https://{AWS_S3_CUSTOM_DOMAIN}/public/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

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
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPagination',
    'PAGE_SIZE': 200,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Smart Cart API',
    'DESCRIPTION': 'E-commerce API for Smart Cart platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': os.path.join(BASE_DIR, 'staticfiles', 'drf_spectacular_sidecar', 'swagger-ui-dist'),
    'SWAGGER_UI_FAVICON_HREF': os.path.join(BASE_DIR, 'staticfiles', 'drf_spectacular_sidecar', 'swagger-ui-dist', 'favicon-32x32.png'),
    'REDOC_DIST': os.path.join(BASE_DIR, 'staticfiles', 'drf_spectacular_sidecar', 'redoc'),
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': None,
    'SERVE_PUBLIC': True,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(weeks=2),
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'VALIDATOR_URL': None,
    'PERSIST_AUTH': True,
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

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]