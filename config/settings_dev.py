"""
Configuration Django pour le développement avec PostgreSQL
"""

from .settings import *

# Mode développement
DEBUG = True

# Base de données PostgreSQL pour le développement
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crm_maroc_dev',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Cache Redis pour le développement
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Celery en mode synchrone pour le développement
CELERY_TASK_ALWAYS_EAGER = True

# Email en console pour le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging plus détaillé
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_dev.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Configuration Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
    '::1',
]

# Configuration pour le développement
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '::1']

# CORS pour le développement
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# CSRF pour le développement
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Configuration des fichiers statiques et media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuration des sessions
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Configuration de sécurité pour le développement
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Configuration des fichiers
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Configuration des tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Configuration des migrations
MIGRATION_MODULES = {}

# Configuration des applications
INSTALLED_APPS += [
    'django_extensions',
]

# Configuration des extensions Django
SHELL_PLUS_MODEL_IMPORTS = {
    'User': 'users.models.User',
    'Company': 'companies.models.Company',
    'Party': 'crm.models.Party',
    'Product': 'catalog.models.Product',
    'Invoice': 'billing.models.Invoice',
}

# Configuration pour le développement
if DEBUG:
    # Désactiver la validation des modèles pour le développement
    import logging
    logging.getLogger('django.db.backends').setLevel(logging.INFO)
    
    # Configuration pour les tests
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]

# Configuration MinIO pour le développement local
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioREDACTED'
MINIO_BUCKET_NAME = 'crm-media-dev'
MINIO_USE_HTTPS = False

# Configuration des fichiers statiques avec whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
