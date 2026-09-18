"""
Configuration Django pour le développement avec SQLite
"""

from .settings import *

# Mode développement
DEBUG = True

# Base de données SQLite pour le développement local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache en mémoire pour le développement
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
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
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Debug Toolbar (déjà dans settings.py principal)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Configuration Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
    '::1',
]

# Configuration pour le développement
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '::1', '10.10.10.15', '0.0.0.0']

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

# Configuration des applications (django_extensions déjà dans settings.py principal)
# INSTALLED_APPS += [
#     'django_extensions',
# ]

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

# Configuration des fichiers statiques avec whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuration des fichiers media en local
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ==============================================================================
# Configuration pour l'environnement de preview Arena
# ==============================================================================
ALLOWED_HOSTS = ['*']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = [
    'https://*.e2b.app',
    'http://*.e2b.app',
    'https://*.arena.ai',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
# Autoriser l'affichage dans l'iframe de prévisualisation
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'django.middleware.clickjacking.XFrameOptionsMiddleware']
X_FRAME_OPTIONS = 'ALLOWALL'
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# Support des sessions et cookies dans les iframes de prévisualisation
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True

# CORS permissif
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Redirection dashboard
LOGIN_REDIRECT_URL = '/'
STATICFILES_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ==============================================================================
# Middleware pour la prévisualisation fluide dans Arena (Iframe)
# ==============================================================================
class AutoLoginMiddleware:
    """Connecte automatiquement en administrateur sur les pages protégées en preview."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/login') and not request.path.startswith('/users/login') and not request.path.startswith('/logout'):
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                from django.contrib.auth import get_user_model, login
                User = get_user_model()
                user = User.objects.filter(username='admin').first()
                if user:
                    login(request, user, backend='users.backends.EmailOrUsernameBackend')
        return self.get_response(request)

# Désactiver la vérification CSRF stricte en preview pour éviter "CSRF cookie not set" dans l'iframe
MIDDLEWARE = [
    m for m in MIDDLEWARE
    if m not in (
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )
]
MIDDLEWARE.append('config.settings_sqlite.AutoLoginMiddleware')

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
