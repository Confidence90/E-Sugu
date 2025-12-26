"""
Django settings for e_sugu project.
"""

from pathlib import Path
from decouple import config
import os
from datetime import timedelta

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
REST_AUTH = {
    'REGISTER_SERIALIZER': 'dj_rest_auth.registration.serializers.RegisterSerializer',
    
}
# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-for-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,192.168.1.145, 192.168.100.57 ', cast=lambda v: [s.strip() for s in v.split(',')])
ALLOWED_HOSTS = ['*']
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'django_filters',
    'django_extensions',
    'rest_framework.authtoken',

    
    # Local apps
    'users',
    'listings',
    'categories',
    'favorites',
    'payments',
    'discussion',
    'notifications',
    'reviews',
    'events',
    'administration',
    'paniers',
    'commandes',
    'livestream',
    'transactions',
    #nouveau
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

AUTHENTICATION_BACKENDS=[
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
SITE_ID = 1
ROOT_URLCONF = 'e_sugu.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'e_sugu.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='e_sugu'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='Confidence00'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Bamako'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Ajouté

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5174",
    "http://localhost:5173",  # Si vous utilisez Vite
    "http://127.0.0.1:8000",
    "http://10.0.2.2:8000",
    "http://localhost:5175",  # 🔥 AJOUTEZ VOTRE PORT
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]
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
    'cache-control',  # 🔥 AJOUTEZ CE HEADER
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]


CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# Twilio (OTP) - Désactivé pour l'instant
# TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
# TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
# TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')
# TWILIO_VERIFY_SERVICE_SID = config('TWILIO_VERIFY_SERVICE_SID', default='')

# Stripe (Payments)
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_CURRENCY = 'xof'
STRIPE_CONNECT_ENABLED = True
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_SECRET_KEY="sk_test_51RGQ0tQPiTasEOUobtCvldqqCKe78sXdNvArOctS3wHqTEeQKuPQ0UynqnfYBfxjg8fmuFmAoE8zkVh8SpTwn0PP009nI7LbE9"
STRIPE_PUBLISHABLE_KEY="pk_test_51RGQ0tQPiTasEOUoLzfyMSAFUH9UTCSSnna0ubGD8BvpMdx0iEMWFQvAwaTG9BklzfABbaoJK23bRn5cIhuLd0eo00UJ7az9t9"

# Agora (Live Streaming)
AGORA_APP_ID = config('AGORA_APP_ID', default='')
AGORA_APP_CERTIFICATE = config('AGORA_APP_CERTIFICATE', default='')

# Security Headers (Production only)
if not DEBUG:
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    #SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Documentation API
SPECTACULAR_SETTINGS = {
    'TITLE': 'E-Sugu API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
EMAIL_BACKEND = config("EMAIL_BACKEND")
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")




GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
SOCIAL_AUTH_PASSWORD = config('SOCIAL_AUTH_PASSWORD')

REST_USE_JWT = True
REST_AUTH_TOKEN_MODEL = None
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'users.views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'google.auth': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
SECURE_CROSS_ORIGIN_OPENER_POLICY = None  # Disable COOP for development
LOGIN_REDIRECT_URL='http://localhost:5173/auth/google/callback/'
ACCOUNT_EMAIL_VERIFICATION='none'
ACCOUNT_AUTHENTICATION='email'

SOCIALACCOUNT_LOGIN_ON_GET= True


SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'picture'
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
    }
}

# Variables Facebook (à mettre dans vos variables d'environnement)
SOCIAL_AUTH_FACEBOOK_KEY = os.getenv('FACEBOOK_APP_ID', 'your_facebook_app_id')
SOCIAL_AUTH_FACEBOOK_SECRET = os.getenv('FACEBOOK_APP_SECRET', 'your_facebook_app_secret')
print(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")
print(f"GOOGLE_CLIENT_ID type: {type(GOOGLE_CLIENT_ID)}")