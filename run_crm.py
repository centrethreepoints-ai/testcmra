#!/usr/bin/env python
"""
Lanceur CRM Maroc pour l'environnement de preview Arena.

Utilise la configuration de développement SQLite (config.settings_sqlite)
et configure les en-têtes nécessaires pour l'affichage en iframe (preview Arena).

Usage:
    /tmp/crm-venv/bin/python run_crm.py runserver 0.0.0.0:8000
    /tmp/crm-venv/bin/python run_crm.py migrate
"""
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.chdir(REPO)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"

import django

django.setup()

from django.conf import settings

# 1. Autoriser n'importe quel hôte derrière le proxy de preview
settings.ALLOWED_HOSTS = ["*"]

# 2. Le proxy de preview est en HTTPS : informer Django du protocole d'origine
settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# 3. Confier la validation CSRF à tous les domaines de preview et plateforme
settings.CSRF_TRUSTED_ORIGINS = list(settings.CSRF_TRUSTED_ORIGINS) + [
    "https://*.e2b.app",
    "http://*.e2b.app",
    "https://*.arena.ai",
]

# 4. Autoriser l'affichage de l'application dans l'iframe de preview Arena
# Retirer le middleware XFrameOptions qui impose X-Frame-Options: DENY
settings.MIDDLEWARE = [
    m for m in settings.MIDDLEWARE
    if m != "django.middleware.clickjacking.XFrameOptionsMiddleware"
]
settings.X_FRAME_OPTIONS = "ALLOWALL"
settings.SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# 5. Autoriser les cookies dans l'iframe de preview (cross-site HTTPS)
settings.SESSION_COOKIE_SAMESITE = "None"
settings.SESSION_COOKIE_SECURE = True
settings.CSRF_COOKIE_SAMESITE = "None"
settings.CSRF_COOKIE_SECURE = True

# 6. CORS permissif pour la prévisualisation
settings.CORS_ALLOW_ALL_ORIGINS = True
settings.CORS_ALLOW_CREDENTIALS = True

# 7. Redirection après connexion vers '/' (dashboard) au lieu de '/dashboard/' (404)
settings.LOGIN_REDIRECT_URL = "/"

# 8. Stockage de fichiers statiques simple pour le dev
settings.STATICFILES_STORAGE = "django.core.files.storage.FileSystemStorage"

from django.core.management import execute_from_command_line

execute_from_command_line(sys.argv)
