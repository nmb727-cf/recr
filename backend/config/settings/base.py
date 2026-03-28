import os
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = 'django-insecure-8y*ihm=-03(z@=$-rcr7l9z&2%9r2c7ux&n20uq9%e39_4avpo'

DEBUG = True

ALLOWED_HOSTS = ['*']

# ─── APPS ────────────────────────────────────────────────────────────────────

SHARED_APPS = [
    'django_tenants',

    # Tenant and auth (must come first)
    'apps.tenants',
    'apps.accounts',

    # RBAC foundation (must come before feature apps so permission classes are importable)
    'apps.rbac',

    # Platform apps
    'apps.organisations',
    'apps.jobs',
    'apps.candidates',
    'apps.pipeline',
    'apps.passport',
    'apps.agencies',
    'apps.interviews',
    'apps.documents',
    'apps.analytics',
    'apps.communications',
    'apps.notifications',
    'apps.automation.apps.AutomationConfig',
    'apps.cafe',
    'apps.marketplace',
    'apps.translations',
    'apps.talent_pools',
    'apps.prequalification',

    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',

    # Testing and Documentation
    'drf_spectacular',
    'django_extensions',
]

TENANT_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

# ─── TENANT CONFIG ────────────────────────────────────────────────────────────

TENANT_MODEL = "tenants.Client"
TENANT_DOMAIN_MODEL = "tenants.Domain"
AUTH_USER_MODEL = 'accounts.CustomUser'

# ─── MIDDLEWARE ───────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'apps.core.middleware.DisallowNonStandardMethodsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ─── TEMPLATES ────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# ─── DATABASE ─────────────────────────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'Admin@123',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)

# ─── AUTH ─────────────────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── JWT ──────────────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
}

# ─── REST FRAMEWORK ───────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# DRF Spectacular (API Documentation & Testing)
# ─────────────────────────────────────────────────────────────

# ─── REST FRAMEWORK ───────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "apps.core.schema.TalentOSAutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.core.authentication.SilentJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 20,

}

SPECTACULAR_SETTINGS = {
    'TITLE': 'TalentOS API',
    'DESCRIPTION': 'Auto-generated API schema for testing and documentation',
    'VERSION': '1.0.0',

    # reduce serializer issues
    'COMPONENT_SPLIT_REQUEST': True,

    # avoid schema recursion issues
    'SERVE_INCLUDE_SCHEMA': False,

    # better endpoint grouping
    'SCHEMA_PATH_PREFIX': r'/api',

    # allow missing serializers gracefully
    'SORT_OPERATIONS': False,
    
}

# ─── INTERNATIONALISATION ─────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ─── SUPPORTED LANGUAGES ──────────────────────────────────────────────────────

LANGUAGES = [
    ('en', 'English'),
    ('hi', 'Hindi'),
    ('mr', 'Marathi'),
    ('fr', 'French'),
    ('de', 'German'),
    ('es', 'Spanish'),
    ('ar', 'Arabic'),
    ('zh', 'Chinese (Simplified)'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ─── STATIC AND MEDIA ─────────────────────────────────────────────────────────

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── REDIS ────────────────────────────────────────────────────────────────────

REDIS_URL = 'redis://localhost:6379'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

# ─── CELERY ───────────────────────────────────────────────────────────────────

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULE = {
    'close-not-interested-engagements': {
        'task': 'apps.candidates.tasks.close_not_interested_engagements',
        'schedule': crontab(minute=0),  # runs every hour
    },
    'expire-candidate-protection-rights': {
        'task': 'apps.candidates.tasks.expire_candidate_protection_rights',
        'schedule': crontab(minute='*/30'),
    },
    'expire-placement-guarantees': {
        'task': 'apps.pipeline.tasks.expire_placement_guarantees_task',
        'schedule': crontab(minute='*/30'),
    },
}

# ─── EMAIL ────────────────────────────────────────────────────────────────────

ENVIRONMENT = 'development'  # 'development' or 'production'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@talentos.dev'
SYSTEM_EMAIL_FROM_NAME = 'TalentOS Notifications'
FRONTEND_URL = 'http://localhost:3000'

# Communication Engine - Email
COMM_EMAIL_MODULE_ENABLED = True
COMM_EMAIL_ENCRYPTION_KEY = os.environ.get('COMM_EMAIL_ENCRYPTION_KEY', '')
COMM_EMAIL_WEBHOOK_SECRET = os.environ.get('COMM_EMAIL_WEBHOOK_SECRET', '')

# Backend callback URIs registered in each provider's console.
# These must be backend URLs (Django), NOT the frontend settings page.
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
GOOGLE_OAUTH_REDIRECT_URI = os.environ.get(
    'GOOGLE_OAUTH_REDIRECT_URI',
    'http://localhost:8000/api/v1/communications/email-accounts/gmail/callback',
)

MICROSOFT_OAUTH_CLIENT_ID = os.environ.get('MICROSOFT_OAUTH_CLIENT_ID', '')
MICROSOFT_OAUTH_CLIENT_SECRET = os.environ.get('MICROSOFT_OAUTH_CLIENT_SECRET', '')
MICROSOFT_OAUTH_REDIRECT_URI = os.environ.get(
    'MICROSOFT_OAUTH_REDIRECT_URI',
    'http://localhost:8000/api/v1/communications/email-accounts/microsoft/callback',
)

# After OAuth callback, backend redirects here.
# Must be explicitly configured to avoid redirecting to the wrong local app.
FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', '')

# ─── OTP ──────────────────────────────────────────────────────────────────────

OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 30

# ─── MINIO ────────────────────────────────────────────────────────────────────

MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin123'
MINIO_USE_HTTPS = False
MINIO_BUCKET_NAME = 'recruitment-platform'


