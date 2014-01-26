import ast
import os
import urlparse
# Import global settings to make it easier to extend settings.
from django.conf.global_settings import *   # pylint: disable=W0614,W0401
import dj_database_url
import dj_redis_url

#==============================================================================
# Generic Django project settings
#==============================================================================

DEBUG = ast.literal_eval(os.environ.get('DEBUG', 'True'))
TEMPLATE_DEBUG = DEBUG
ASSETS_DEBUG = DEBUG

SITE_ID = 1
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'UTC'
USE_TZ = True
USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', 'English'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ['SECRET_KEY']
AUTH_USER_MODEL = 'accounts.User'
INSTALLED_APPS = (
    'botbot.apps.accounts',
    'botbot.apps.bots',
    'botbot.apps.logs',
    'botbot.apps.plugins',
    'botbot.core',

    'django_hstore',
    'south',
    'launchpad',
    'social_auth',
    'django_assets',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
)

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

#==============================================================================
# Calculation of directories relative to the project module location
#==============================================================================

import os
import sys
import botbot as project_module

PROJECT_DIR = os.path.dirname(os.path.realpath(project_module.__file__))

PYTHON_BIN = os.path.dirname(sys.executable)
ve_path = os.path.dirname(os.path.dirname(os.path.dirname(PROJECT_DIR)))
# Assume that the presence of 'activate_this.py' in the python bin/
# directory means that we're running in a virtual environment.
if os.path.exists(os.path.join(PYTHON_BIN, 'activate_this.py')):
    # We're running with a virtualenv python executable.
    VAR_ROOT = os.path.join(os.path.dirname(PYTHON_BIN), 'var')
elif ve_path and os.path.exists(os.path.join(ve_path, 'bin',
                                             'activate_this.py')):
    # We're running in [virtualenv_root]/src/[project_name].
    VAR_ROOT = os.path.join(ve_path, 'var')
else:
    # Set the variable root to the local configuration location (which is
    # ignored by the repository).
    VAR_ROOT = os.path.join(PROJECT_DIR, 'conf', 'local')

if not os.path.exists(VAR_ROOT):
    os.mkdir(VAR_ROOT)

#==============================================================================
# Project URLS and media settings
#==============================================================================

ROOT_URLCONF = 'botbot.urls'

LOGIN_URL = '/dashboard/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/dashboard/'
INCLUDE_DJANGO_ADMIN = ast.literal_eval(os.environ.get(
                                        'INCLUDE_DJANGO_ADMIN', 'True'))

STATIC_URL = '/static/'
MEDIA_URL = '/uploads/'

STATIC_ROOT = os.environ.get('STATIC_ROOT', os.path.join(VAR_ROOT, 'static'))
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(VAR_ROOT, 'uploads'))

STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)

DATABASES = {'default': dj_database_url.config(
    default='postgres://localhost:5432/botbot')}
# Reuse database connections
DATABASES['default']['CONN_MAX_AGE'] = None

#==============================================================================
# Templates
#==============================================================================
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS += (
    "django.core.context_processors.request",
    "django.core.context_processors.tz",
)

#==============================================================================
# Middleware
#==============================================================================

MIDDLEWARE_CLASSES += (
    'botbot.core.middleware.TimezoneMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

#==============================================================================
# Auth / security
#==============================================================================

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
AUTHENTICATION_BACKENDS += (
    'social_auth.backends.google.GoogleBackend',
    'django.contrib.auth.backends.ModelBackend',
)

#==============================================================================
# Logger project settings
#==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': []
        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'botbot.plugin_runner': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

#=============================================================================
# Cache
#=============================================================================
if 'MEMCACHE_URL' in os.environ:
    DEFAULT_CACHE = {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': os.environ['MEMCACHE_URL'],
    }
else:
    DEFAULT_CACHE = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'botbot',
    }

CACHES = {
    'default': DEFAULT_CACHE
}

#=============================================================================
# Email
#=============================================================================

ADMINS = (
    ('LL', 'info@lincolnloop.com'),
)
EMAIL_SUBJECT_PREFIX = "[BBME] "

if 'SMTP_URL' in os.environ:
    url = urlparse.urlparse(os.environ['SMTP_URL'])
    EMAIL_HOST = url.hostname
    EMAIL_HOST_USER = url.username
    EMAIL_HOST_PASSWORD = url.password
    EMAIL_PORT = url.port or 25
    EMAIL_USE_TLS = ast.literal_eval(os.environ.get('SMTP_TLS', 'False'))
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#==============================================================================
# Miscellaneous project settings
#==============================================================================

# Above this many users is considered a big channel, display is different
BIG_CHANNEL = 25
# Nicks requested to be excluded from logging
EXCLUDE_NICKS = os.environ.get('EXCLUDE_NICKS', '').split(',')
if EXCLUDE_NICKS == ['']:
    EXCLUDE_NICKS = []

REDIS_PLUGIN_QUEUE_URL = os.environ.get('REDIS_PLUGIN_QUEUE_URL',
                                        'redis://localhost:6379/0')
REDIS_PLUGIN_STORAGE_URL = os.environ.get('REDIS_PLUGIN_STORAGE_URL',
                                          'redis://localhost:6379/1')

#==============================================================================
# Third party app settings
#==============================================================================

SOUTH_DATABASE_ADAPTERS = {'default': 'south.db.postgresql_psycopg2'}

REDIS_SSEQUEUE = dj_redis_url.config('REDIS_SSEQUEUE_URL',
                                     'redis://localhost:6379/2')

REDIS_SSEQUEUE_CONNECTION_SETTINGS = {
    'location': '{HOST}:{PORT}'.format(**REDIS_SSEQUEUE),
    'password': REDIS_SSEQUEUE['PASSWORD'],
    'db': REDIS_SSEQUEUE['DB'],
}

SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email']
SOCIAL_AUTH_DEFAULT_USERNAME = 'user'
SOCIAL_AUTH_ASSOCIATE_BY_MAIL = True
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/accounts/manage/'
