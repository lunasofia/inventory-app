"""
Django settings for the packing & inventory app.

Configuration is driven by environment variables (via django-environ) so the
same code runs locally (SQLite by default) and on GCP Cloud Run (Cloud SQL
Postgres + Cloud Storage + Secret Manager).
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['*']),
    SECRET_KEY=(str, 'django-insecure-dev-key-change-me'),
)

# Read a local .env file if present (not committed). In production, env vars
# come from Cloud Run / Secret Manager instead.
env_file = BASE_DIR / '.env'
if env_file.exists():
    env.read_env(str(env_file))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Cloud Run serves behind https; trust the host it provides.
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'accounts',
    'catalog',
    'trips',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'trips.context_processors.sidebar',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Use DATABASE_URL if provided (e.g. postgres://... on Cloud SQL), else SQLite.
DATABASES = {
    'default': env.db_url(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
    )
}

# Guard against silently running on ephemeral in-container SQLite in production
# (Cloud Run wipes the container filesystem on every new revision -> data loss).
# Set REQUIRE_REAL_DB=True at runtime on Cloud Run; leave unset for build/local/tests.
if env.bool('REQUIRE_REAL_DB', default=False) and 'sqlite' in DATABASES['default']['ENGINE']:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        'REQUIRE_REAL_DB is set but the database resolved to SQLite. '
        'DATABASE_URL (the Cloud SQL connection) is missing — refusing to start '
        'on ephemeral storage to avoid data loss.'
    )

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom user model (email-based login). Set before first migration.
AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (served by WhiteNoise in production)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
# In production use WhiteNoise's hashed-manifest storage (needs collectstatic);
# in local dev use the plain storage so the dev server works without it.
_staticfiles_backend = (
    'django.contrib.staticfiles.storage.StaticFilesStorage'
    if DEBUG
    else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
)
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': _staticfiles_backend},
}

# Media files. Locally on disk; on GCP overridden to Cloud Storage via env.
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Production hardening — only when DEBUG is off (i.e. on Cloud Run).
# Cloud Run terminates TLS and forwards X-Forwarded-Proto, so trust it.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Opt-in HSTS (0 = off by default to avoid locking out a custom domain early).
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
