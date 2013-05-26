import os
from ConfigParser import RawConfigParser

config = RawConfigParser()

try:
    # production system
    config.readfp(open('/etc/submit/settings.ini')) 
except IOError:
    try:
        # development machine
        config.readfp(open('submit/settings_dev.ini'))
    except:
        print("No configuration file found.")
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
SCRIPTS_ROOT = os.getcwd()
DEBUG = bool(config.get('general', 'DEBUG'))
FORCE_SCRIPT_NAME = config.get('server', 'FORCE_SCRIPT_NAME')
EMAIL_BACKEND = 'django.core.mail.'+config.get('server', 'EMAIL_BACKEND')+'.smtp.EmailBackend'    
MAIN_URL = config.get('server', 'MAIN_URL') 
MEDIA_ROOT = config.get('server', 'MEDIA_ROOT')
MEDIA_URL = MAIN_URL + '/files/'
STATIC_ROOT = SCRIPTS_ROOT + '/static/'
STATIC_URL = MAIN_URL + '/static/'
STATICFILES_DIRS = (STATIC_ROOT)

TEMPLATE_DEBUG = DEBUG
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

