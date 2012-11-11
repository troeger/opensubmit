import os

is_production = False
cwd = os.path.dirname(__file__)

if cwd.startswith('/usr/local'):
    is_production = True

if is_production:
    DEBUG = False
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql_psycopg2', 
            'NAME':     'submit',
            'USER':     'submit',                           
            'PASSWORD': 'submit',                           
            'HOST':     '',                           
            'PORT':     '',                           
        }
    }
    MEDIA_ROOT = '/data/submit/'
    MEDIA_URL = 'http://www.dcl.hpi.uni-potsdam.de/submit/files/'
    STATIC_ROOT = '/var/www/submit/submit/static/'
    STATIC_URL = 'http://www.dcl.hpi.uni-potsdam.de/submit/static/'
    STATICFILES_DIRS = ("/var/www/submit/submit/static")
    FORCE_SCRIPT_NAME="/submit"
    MAIN_URL = 'http://www.dcl.hpi.uni-potsdam.de/submit/' 
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'    
else:
    DEBUG = True
    DATABASES = {
        'default': {
        'ENGINE':   'django.db.backends.sqlite3', 
        'NAME':     'database.sqlite',
        }
    }
    MEDIA_ROOT = 'media/'
    MEDIA_URL = '/media/'
    STATIC_ROOT = 'static/'
    STATIC_URL = '/static/'
    MAIN_URL = 'http://localhost:8000/' 
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Global settings
TEMPLATE_DEBUG = DEBUG
ADMINS = (('Peter Troeger', 'peter.troeger@hpi.uni-potsdam.de'),)
MANAGERS = ADMINS
EMAIL_SUBJECT_PREFIX = '[Submit] '
TIME_ZONE = "Europe/Berlin"
LANGUAGE_CODE = 'en-en'
USE_I18N = True
USE_L10N = True
USE_TZ = False
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
SECRET_KEY = 'uzfp=4gv1u((#hb*#o3*4^v#u#g9k8-)us2nw^)@rz0-$2-23)'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)
ROOT_URLCONF = 'submit.urls'
WSGI_APPLICATION = 'submit.wsgi.application'
TEMPLATE_DIRS = ()
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'openid2rp.django',
    'south',
    'submit'
)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'openid2rp.django.auth.Backend'
)
JOB_EXECUTOR_SECRET="49845zut93purfh977TTTiuhgalkjfnk89"
assert(JOB_EXECUTOR_SECRET is not "")

