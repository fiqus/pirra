"""Development settings and globals."""
from .common import *

HACK_SSL_UBUNTU_15 = True

DEBUG = True
TEMPLATE_DEBUG = DEBUG
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SITE_URL = 'localhost'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'pass',
        'HOST': 'localhost',
        'PORT': '',
    },
}

REDIS_URL = "redis://localhost:6379/0"

SECRET_KEY = "" #Usar string random

CUIT_TO_CONNECT = ''  # CUIT relacionado al computador del propietario de la private key / certificate

PRIVATE_KEY = b"""[Aquí su clave]"""  #Clave AFIP

CERTIFICATE = b"""[Aquí su certificado]"""  #Certificado de la AFIP

# INSTALLED_APPS = INSTALLED_APPS +  ("sample_hooks",)
