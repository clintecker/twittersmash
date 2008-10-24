import sys
from os import path as os_path

# This is the path where this settings.py lives
PROJECT_PATH = os_path.abspath(os_path.split(__file__)[0])
ROOT_PATH = os_path.join(PROJECT_PATH, '../')

if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

# This calculates where the vendor path is and adds it to the python path
VENDOR_PATH = os_path.join(PROJECT_PATH, 'vendor')
if VENDOR_PATH not in sys.path:
    sys.path.insert(0, VENDOR_PATH)


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Clint Ecker', 'clint@arstechnica.com'),
    ('Kurt Mackey', 'kurt@arstechnica.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os_path.join(PROJECT_PATH, 'smash.db')

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False

DEFAULT_CHARSET = 'utf-8'

MEDIA_ROOT = os_path.join(PROJECT_PATH, 'static')
MEDIA_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/media/'

SECRET_KEY = '62pgc6w9$_lt0&ve4oe+id=g0*i*=ya1_@-fakjda&!4dr472v'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'twittersmash.urls'

TEMPLATE_DIRS = (
)

REUSABLE_APPS_DIRS = (
	VENDOR_PATH,
)

INSTALLED_APPS = (
    ## core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_extensions',
	'django_evolution',
    'smash',
)

FORCE_SCRIPT_NAME = ''