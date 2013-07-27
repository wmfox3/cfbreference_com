import os
import log
import sys

PROJECT_PATH = os.path.dirname( __file__ )
PROJECT_DIR = os.path.dirname( __file__ )
sys.path.append( PROJECT_PATH )

'''
if os.environ.has_key('ENV') and os.environ['ENV'].lower() == "pro":
    from envs.pro_settings import *
else:
    from envs.local_settings import *
'''

# Start Logging
#log.init_logging(LOGGING_DIR)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

INTERNAL_IPS = ( '127.0.0.1', )
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,       
}

SITE_ID = 1

# Django Default Date Format Override
DATE_FORMAT = 'N j, Y'

# Admins get notified of 500 errors
ADMINS = (
('name', 'mail@mail.com'),
)

# Managers get notified of 404 errors
MANAGERS = ADMINS

DOCS_ROOT = os.path.join(PROJECT_PATH, 'docs/_build/html')

DATABASES = {
    'default': {
        'ENGINE': '',                    # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Default email address 500 / 404 emails get sent from
SERVER_EMAIL = 'mail@mail.com'

# Email admins when users hit a 404
SEND_BROKEN_LINK_EMAILS = False

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Root directory for local static file serving.
STATIC_DOC_ROOT = ""

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = ''

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/media/static/admin/'

# List of callables that know how to import templates from various sources.
#TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.load_template_source',
#    'django.template.loaders.app_directories.load_template_source',
#)
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)


ROOT_URLCONF = 'cfbreference_com.urls'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',    
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates').replace('\\', '/'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.markup',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django_extensions',
    'debug_toolbar',
    'common',
    'college',
    'blog',
    'rankings',
    'scrapers',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

CURRENT_SEASON = 2012
URL_CACHE_TIME = 1440
XML_CACHE_TIME = 1440

EMAIL_SUBJECT_PREFIX = '[College Football Reference] '