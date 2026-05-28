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

    # RBAC foundation
    'apps.rbac',

    # Platform apps
    'apps.organisations',
    'apps.jobs',
    'apps.candidates',
    'apps.pipeline',
    'apps.passport',
    'apps.agencies',
    'apps.agency_candidates',
    'apps.interviews',
    'apps.documents',
    'apps.analytics',
    'apps.communications',
    'apps.notifications',
    'apps.automation',
    'apps.cafe',
    'apps.marketplace',
    'apps.translations',
    'apps.talent_pools',
    'apps.prequalification',
    'apps.module_registry',
    'apps.orchestration_center',
    'apps.integrations',
    'apps.hdc',
    'apps.automation_command_center',
    'apps.automation_permissions',
    'apps.automation_notifications',
    'apps.automation_tasks',
    'apps.automation_sla',
    'apps.automation_playbooks',
    'apps.automation_sandbox',
    'apps.automation_change_impact',
    'apps.automation_observability',
    'apps.automation_recovery',
    'apps.automation_os',
    'apps.automation_maturity',
    'apps.executive_automation',
    'apps.automation_learning',
    'apps.automation_ai_brain',
    'apps.automation_system_completion',
    'apps.recruiter_workspace',
    'apps.qa',
    'apps.agency_workflows',
    'apps.workflow_execution',

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
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASS', 'Admin@123'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
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
    'process-due-passport-withdrawal-deletions': {
        'task': 'passport.process_due_withdrawal_deletions',
        'schedule': crontab(minute='*/30'),
    },
}

# ─── EMAIL ────────────────────────────────────────────────────────────────────

ENVIRONMENT = 'development'  # 'development' or 'production'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@talentos.dev'
SYSTEM_EMAIL_FROM_NAME = 'TalentOS Notifications'
FRONTEND_URL = 'http://localhost:5173'
FRONTEND_BASE_URL = 'http://localhost:5173'

# ─── OTP ──────────────────────────────────────────────────────────────────────

OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 30

# ─── MINIO ────────────────────────────────────────────────────────────────────

MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin123'

# External workflow callback request signing
WORKFLOW_CALLBACK_SIGNATURE_SECRET = os.getenv('WORKFLOW_CALLBACK_SIGNATURE_SECRET', SECRET_KEY)
WORKFLOW_CALLBACK_SIGNATURE_TTL_SECONDS = int(os.getenv('WORKFLOW_CALLBACK_SIGNATURE_TTL_SECONDS', '300'))
INTERVIEW_SCHEDULING_PUBLIC_RATE_WINDOW_SECONDS = int(os.getenv('INTERVIEW_SCHEDULING_PUBLIC_RATE_WINDOW_SECONDS', '60'))
INTERVIEW_SCHEDULING_PUBLIC_GET_RATE_LIMIT = int(os.getenv('INTERVIEW_SCHEDULING_PUBLIC_GET_RATE_LIMIT', '30'))
INTERVIEW_SCHEDULING_PUBLIC_POST_RATE_LIMIT = int(os.getenv('INTERVIEW_SCHEDULING_PUBLIC_POST_RATE_LIMIT', '10'))
PUBLIC_PASSPORT_RATE_WINDOW_SECONDS = int(os.getenv('PUBLIC_PASSPORT_RATE_WINDOW_SECONDS', '60'))
PUBLIC_PASSPORT_RATE_LIMIT = int(os.getenv('PUBLIC_PASSPORT_RATE_LIMIT', '30'))
CANDIDATE_CLAIM_RATE_WINDOW_SECONDS = int(os.getenv('CANDIDATE_CLAIM_RATE_WINDOW_SECONDS', '60'))
CANDIDATE_CLAIM_GET_RATE_LIMIT = int(os.getenv('CANDIDATE_CLAIM_GET_RATE_LIMIT', '30'))
CANDIDATE_CLAIM_POST_RATE_LIMIT = int(os.getenv('CANDIDATE_CLAIM_POST_RATE_LIMIT', '20'))
CANDIDATE_IDENTITY_CHECK_RATE_WINDOW_SECONDS = int(os.getenv('CANDIDATE_IDENTITY_CHECK_RATE_WINDOW_SECONDS', '60'))
CANDIDATE_IDENTITY_CHECK_RATE_LIMIT = int(os.getenv('CANDIDATE_IDENTITY_CHECK_RATE_LIMIT', '60'))
CANDIDATE_PUBLIC_APPLY_RATE_WINDOW_SECONDS = int(os.getenv('CANDIDATE_PUBLIC_APPLY_RATE_WINDOW_SECONDS', '60'))
CANDIDATE_PUBLIC_APPLY_GET_RATE_LIMIT = int(os.getenv('CANDIDATE_PUBLIC_APPLY_GET_RATE_LIMIT', '60'))
CANDIDATE_PUBLIC_APPLY_POST_RATE_LIMIT = int(os.getenv('CANDIDATE_PUBLIC_APPLY_POST_RATE_LIMIT', '20'))
MINIO_USE_HTTPS = False
MINIO_BUCKET_NAME = 'recruitment-platform'
