import os
from ConfigParser import RawConfigParser

config = RawConfigParser()

# Determine dev mode based on the existence of the dev settings file,
# since this is excluded from the source code distribution.
try:
    # production system
    config.readfp(open('/etc/submit/settings.ini')) 
    is_production = True
except IOError:
    try:
        # development machine
        config.readfp(open('submit/settings_dev.ini'))
        is_production = False
        print "Using submit/settings_dev.ini"
    except:
        # See if the user just forgot to edit and rename the template
        try:
            config.readfp(open('submit/settings.ini.template'))
            print("No configuration file found. Please copy .../submit/settings.ini.template to /etc/submit/settings.ini and edit it.")
            exit(-1)
        except:
            print("Error - Configuration file /etc/submit/settings.ini does not exist.")
            exit(-1)

# Global settings
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.'+config.get('database', 'DATABASE_ENGINE'), 
        'NAME':     config.get('database', 'DATABASE_NAME') ,
        'USER':     config.get('database', 'DATABASE_USER') ,                           
        'PASSWORD': config.get('database', 'DATABASE_PASSWORD') ,                           
        'HOST':     config.get('database', 'DATABASE_HOST'),                           
        'PORT':     config.get('database', 'DATABASE_PORT'),                           
    }
}

DEBUG = bool(config.get('general', 'DEBUG'))
TEMPLATE_DEBUG = DEBUG

# Let the user specify the complete URL, and split it up accordingly
# FORCE_SCRIPT_NAME is needed for handling subdirs accordingly on Apache
MAIN_URL = config.get('server', 'HOST') + config.get('server','HOST_DIR')
url = MAIN_URL.split('/')
FORCE_SCRIPT_NAME = config.get('server','HOST_DIR')

MEDIA_ROOT = config.get('server', 'MEDIA_ROOT')
MEDIA_URL = MAIN_URL + '/files/'

if is_production:
    STATIC_ROOT = config.get('server', 'SCRIPT_ROOT') +'static/'
    STATIC_URL = MAIN_URL+'/static/'
    STATICFILES_DIRS = (config.get('server', 'SCRIPT_ROOT') +'static',)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'    
    ALLOWED_HOSTS = [MAIN_URL.split('/')[2]]
else:
    STATIC_ROOT = 'static/'
    STATIC_URL = '/static/'
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'    
    ALLOWED_HOSTS = ['localhost']

LOGIN_DESCRIPTION = config.get('login','LOGIN_DESCRIPTION')
OPENID_PROVIDER = config.get('login','OPENID_PROVIDER')

ADMINS = ( (config.get('admin', 'ADMIN_NAME'), config.get('admin', 'ADMIN_EMAIL')),)
MANAGERS = ADMINS
EMAIL_SUBJECT_PREFIX = '[Submit] '
TIME_ZONE = config.get("server", "TIME_ZONE")
LANGUAGE_CODE = 'en-en'
USE_I18N = True
USE_L10N = True
USE_TZ = False
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
SECRET_KEY = config.get("server","SECRET_KEY")
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
TEMPLATE_DIRS = (
    'submit/templates/'
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'openid2rp.django',
    'bootstrapform',
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

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'submit.contextprocessors.footer'
)

JOB_EXECUTOR_SECRET=config.get("executor","SHARED_SECRET")
assert(JOB_EXECUTOR_SECRET is not "")

