# Django settings for pirra_web project.
from django.contrib import messages
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("BASE DIR:", BASE_DIR)
DEBUG = True
TEMPLATE_DEBUG = DEBUG

URL_CUENTAS = 'https://metoikion.bantics.ar/api'

SECRET_KEY = 'zom3yqi7+rp=u_x060fga^*$banti@-w2xvzu1y^sw1$$wv99e'


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Argentina/Buenos_Aires'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es-ar'

DATE_FORMAT = 'j N, Y'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/../../media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/../../static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.dirname(os.path.abspath(__file__)) + '/../../bower_components/',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets'),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (os.path.join(os.path.dirname(__file__), '../..', 'templates').replace('\\', '/'),),
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            )
        },
    },
]

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'hooks.middleware.HookMiddleware'
)

ROOT_URLCONF = 'pirra_web.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'pirra_web.wsgi.application'

INSTALLED_APPS = (

    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.admin',
    'django.contrib.sitemaps',

    'bootstrap4',
    'django_tables2',
    'ckeditor',
    'adminsortable2',
    'captcha',
    'webpack_loader',
    'rest_framework',
    'rest_framework.authtoken',

    'hooks',
    'main',
    'afip',
    'pirra_web',
    'help',
    'empresa',
    'comprobante',
    'django.contrib.auth',
)

DEMO = False

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

MESSAGE_TAGS = {messages.DEBUG: 'warning',
                messages.INFO: 'info',
                messages.SUCCESS: 'success',
                messages.WARNING: 'warning',
                messages.ERROR: 'error', }

WSAA_URL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
WSFE_URL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
WSFEX_URL = "http://wswhomo.afip.gov.ar/WSFEXv1/service.asmx"

PADRON_URL = "http://www.afip.gob.ar/genericos/cInscripcion/archivos/apellidoNombreDenominacion.zip"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = '/accounts/login'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

REDIS_URL = "redis://localhost:6379/0"

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_JQUERY_URL = '//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js'

DEFAULT_FROM_EMAIL = "noreply@mailer.aquiles.com.ar"
CONTACT_EMAIL = "info@aquiles.com.ar"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.bantics.com.ar'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'rfpolverini@bantics.com.ar'
EMAIL_HOST_PASSWORD = 'zebra682'



CAPTCHA_IMAGE_SIZE = (200, 50)
CAPTCHA_FONT_SIZE = 30

MONEDA_LOCAL_CTZ = 1
MONEDA_LOCAL = "PES"

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'TEST_REQUEST_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'webpack_bundles/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': [r'.+\.hot-update.js', r'.+\.map']
    }
}

DJANGO_TABLES2_TEMPLATE = "table_template.html"


PRIVATE_KEY = b"""-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA3g56TUcVA9Zy1BcFcigVsKo0osPKxcDcL1uWw/MbvLkMa198
J7dU6oSB2nc7dHFIFNBWVO4CnRc0SygzsK5roO/wL+rzI/hCwwt4UUCDkdhDs7Gw
jwcH18tBOYSLGH1fYckox1maaFmAm01ErQnpS1ITCd8g4fEVuwbvMWCGlWaWkDTL
Xc9BCm6gloeZ1GXcz/SQbTclwJTY6gwrTMN22eukr/6iWwH7e7e7racC8KI3S0Em
gm8ANcqAmya1p25z79UQrSG+16ue7E+2QARPDgU2ef1S4ss0sIGF1H+dL0S2EGFM
4ZhOrS3ryB9+rkXJeQkbCVEyKo55vdfu/lXkTQIDAQABAoIBAE+r7iGv8VBRLx39
rIyK6U1bpEsJ6MUPL3EmcW+Y2EjcNCKKPeeaFbOXG2ghA4oB4xTkszUBuJpYawDU
SceIrUEvFYR7zgUH3BxTDzZH6Wz4pUHh7TFEGoJIgPx8G9QLl59kJ2dvNMFf647N
KGjVd4j4x6/xCMFIWL2j/UpAEcmkPBFyuDahlWEIAnlbmyDSoZfUWFjXMxQiwS7y
IY4BesG1oQwrs54+x6IZ2I0Pq4rzrjSkKBSzMewC2BypFOwvjJVXNLZNDpeHfosk
LlxsXbHLTpGi5KI3o/mPXppiW1dtYKsk7pm2c2tHkeWNBz6URDTw+2BGYchpp2+T
rXfHnNkCgYEA9c8wWochp1won6me4Hlpj/Bz7F6XYPTEyJTjT66kSGLa4xjjekEm
my61a92waCutGvCfnbcMLq0AOEcNmPHT5/FiiKOzVsoqgkOQTq66bKA7WOEiUEuV
t0Tq5eDzlnc4pczWj7ICa2xCps9i1KhYUZepL/VQ/fLfahX+1PRSKX8CgYEA50My
dBcLiMyL3F+SS/T0N66C1o99Nr+DGWTdxle8ct3sQRo+ishUa63d2sQM5RQBqXKf
TjZe75dqBGXwo2m3Gzcgyk0hRbVW5A+Z9U+36JbYCWWKGBHcQcR6Yb62UJnyf99+
WivZxH1PX+p8jVQ2HtUPLQTIgTl0JEMx/qGYYDMCgYEAw1FFn7lecWiWUv/p4X43
9grfYgNrj7wOnT9JO+iOW4JJYUhGgL9CGO7Nc49s++kwnIZ0nlJz2KbY1N8Im+4U
LmosnFxPRXhQvL9I7GyEb4oGfkIuDNVyenTFnbHYfEfxeDVCjF2q9IbKk1eYtVer
DfJPmm74U0FoaxhdLAOTQasCgYEAy7azwPNz46NbKFq/wk0au9nrwxlO0WVOFJZ3
jXpHtF+s94Qox5PEWb4kicrdGQXQmPUxQ3I9mowkhY9OtIQxGbYsGkhrIL6mterQ
UflRJX+K+mwJgz5oaT6sF2Ips0KJDP9QjBnIkH9Z5kHmSZB+xBYmch+eh8aWekL+
zTCHy2UCgYB1mBi8JafcWTtRa9XN3v76T76e8spbw3Oy0eScBwMaLPmT2kHWcwDD
FUsDw73w9gq/+H/XBeG/iLIw6gCdiDhn8TGREPUEuSqcc+S871PoY93RK78tkY0y
uXodkUzbNJk9YbJle8MQHyaKv2hTZkruaqfer51/vxrO7zq+DOdLzg==
-----END RSA PRIVATE KEY-----"""

CERTIFICATE = b"""-----BEGIN CERTIFICATE-----
MIIDSzCCAjOgAwIBAgIIDtCZS4gWHcMwDQYJKoZIhvcNAQENBQAwODEaMBgGA1UEAwwRQ29tcHV0
YWRvcmVzIFRlc3QxDTALBgNVBAoMBEFGSVAxCzAJBgNVBAYTAkFSMB4XDTE5MTAxODIwMjg0MloX
DTIxMTAxNzIwMjg0MlowMTEUMBIGA1UEAwwLQmFudGljczIwMTkxGTAXBgNVBAUTEENVSVQgMjAx
MTg2MjAxMjgwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDeDnpNRxUD1nLUFwVyKBWw
qjSiw8rFwNwvW5bD8xu8uQxrX3wnt1TqhIHadzt0cUgU0FZU7gKdFzRLKDOwrmug7/Av6vMj+ELD
C3hRQIOR2EOzsbCPBwfXy0E5hIsYfV9hySjHWZpoWYCbTUStCelLUhMJ3yDh8RW7Bu8xYIaVZpaQ
NMtdz0EKbqCWh5nUZdzP9JBtNyXAlNjqDCtMw3bZ66Sv/qJbAft7t7utpwLwojdLQSaCbwA1yoCb
JrWnbnPv1RCtIb7Xq57sT7ZABE8OBTZ5/VLiyzSwgYXUf50vRLYQYUzhmE6tLevIH36uRcl5CRsJ
UTIqjnm91+7+VeRNAgMBAAGjYDBeMAwGA1UdEwEB/wQCMAAwHwYDVR0jBBgwFoAUs7LT//3put7e
ja8RIZzWIH3yT28wHQYDVR0OBBYEFGgQgULM8qVNqQv4JaOkI8hxgLhYMA4GA1UdDwEB/wQEAwIF
4DANBgkqhkiG9w0BAQ0FAAOCAQEAONpPPQl7C4iXnpc+I0cNnhQoFSHms1eBh9+2+VZGy9gw+dEb
a6dVHjdNEWawv3EJqbcnLyH9zCb5QgbxCQxUlTpIDVOh0tizhIYldo+v1yP4xfuhiygWufts7IzN
Dibfgs6ZHnuTjhcR7GUwRcZ9ot68ixWFVIAmR8RM/oHePdnxnwoQonuI251ZOqXVG9vFwxjjZ12X
i2TbptGoPVCh90fl6KuEYoBG3rerKkhrRyMroVGWP6gRzBM1i7ClpyexLk9f5chTlualP7TNfW4J
g0hiAjp0nNiMLNlB18CoKnOOm1D5tlJ/BI3bRklT7+bUswPLgoQTr0XLl0m9Pi/wqA==
-----END CERTIFICATE-----"""
