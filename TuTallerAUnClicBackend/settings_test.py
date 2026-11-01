"""Configuracion solo para correr las pruebas (local o en GitHub Actions).

Usa SQLite en memoria para no necesitar MySQL. Uso:
    python manage.py test TuTallerApp --settings=TuTallerAUnClicBackend.settings_test
"""
import os

os.environ.setdefault('SECRET_KEY', 'clave-solo-para-pruebas')

from .settings import *  # noqa: E402,F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
SECURE_SSL_REDIRECT = False
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
