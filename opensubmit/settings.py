from __future__ import print_function

import sys
import os
from ConfigParser import SafeConfigParser


# The following section determines which configuration file to load.
# It also deduces whether we are in a live environment (is_production,
# which forces DEBUG to False), or in a development environment (al-
# lowing DEBUG mode).
def find_config_info():
    config_info_default = (os.path.abspath('opensubmit/settings.ini.template'), False, )

    # config_info: (<config file path>, <is production>, )
    system_config_directories = {
        'win32': os.path.expandvars('$APPDATA'),
        'default': '/etc',
    }

    if sys.platform in system_config_directories:
        system_config_directory = system_config_directories[sys.platform]
    else:
        system_config_directory = system_config_directories['default']

    config_directories = [
        os.path.join(os.path.dirname(__file__)),
        os.path.join(system_config_directory, 'opensubmit'),
    ]

    config_files = (
        ('settings_dev.ini', False, ),
        ('settings.ini', True, ),
    )

    for config_file, production in config_files:
        for config_path in config_directories:
            config_file_path = os.path.join(config_path, config_file)
            if os.path.isfile(config_file_path):
                return (config_file_path, production, )

    print("No configuration file found. Falling back to default settings, which most likely will not work.", file=sys.stderr)
    return config_info_default

config_file_path, is_production = find_config_info()
try:
    config_fp = open(config_file_path, 'r')
except IOError:
    print("ERROR: Cannot open configuration file {}! Exiting.".format(config_file_path), file=sys.stderr)
    sys.exit(-1)

print("Choosing {} as configuration file".format(config_file_path), file=sys.stderr)

config = SafeConfigParser()
config.readfp(config_fp)

# Global settings
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.' + config.get('database', 'DATABASE_ENGINE'),
        'NAME':     config.get('database', 'DATABASE_NAME'),
        'USER':     config.get('database', 'DATABASE_USER'),
        'PASSWORD': config.get('database', 'DATABASE_PASSWORD'),
        'HOST':     config.get('database', 'DATABASE_HOST'),
        'PORT':     config.get('database', 'DATABASE_PORT'),
    }
}

if bool(config.get('general', 'DEBUG')) and is_production:
    print("WARNING: DEBUG is enabled in configuration file, despite being in productive mode.", file=sys.stderr)

DEBUG = bool(config.get('general', 'DEBUG')) and not is_production
TEMPLATE_DEBUG = DEBUG

# Let the user specify the complete URL, and split it up accordingly
# FORCE_SCRIPT_NAME is needed for handling subdirs accordingly on Apache
MAIN_URL = config.get('server', 'HOST') + config.get('server', 'HOST_DIR')
url = MAIN_URL.split('/')
FORCE_SCRIPT_NAME = config.get('server', 'HOST_DIR')

MEDIA_ROOT = config.get('server', 'MEDIA_ROOT')
MEDIA_URL = MAIN_URL + '/files/'

if is_production:
    STATIC_ROOT = config.get('server', 'SCRIPT_ROOT') + 'static/'
    STATIC_URL = MAIN_URL + '/static/'
    STATICFILES_DIRS = (STATIC_ROOT, )
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    ALLOWED_HOSTS = [MAIN_URL.split('/')[2]]
else:
    STATIC_ROOT = 'static/'
    STATIC_URL = '/static/'
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    ALLOWED_HOSTS = ['localhost']

LOGIN_DESCRIPTION = config.get('login', 'LOGIN_DESCRIPTION')
OPENID_PROVIDER = config.get('login', 'OPENID_PROVIDER')

ADMINS = (
    (config.get('admin', 'ADMIN_NAME'), config.get('admin', 'ADMIN_EMAIL'), ),
)
MANAGERS = ADMINS
EMAIL_SUBJECT_PREFIX = '[OpenSubmit] '
TIME_ZONE = config.get("server", "TIME_ZONE")
LANGUAGE_CODE = 'en-en'
USE_I18N = True
USE_L10N = True
USE_TZ = False
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)
SECRET_KEY = config.get("server", "SECRET_KEY")
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEST_RUNNER = 'opensubmit.tests.DiscoverRunner'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)
ROOT_URLCONF = 'opensubmit.urls'
WSGI_APPLICATION = 'opensubmit.wsgi.application'
TEMPLATE_DIRS = (
    'opensubmit/templates/',
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'grappelli',    
    'django.contrib.admin.apps.SimpleAdminConfig',
    'openid2rp.django',
    'bootstrapform',
    'rest_framework',
    'opensubmit',
#    'executor_api',
)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level':   'DEBUG',
            'class':   'logging.StreamHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'OpenSubmit': {
            'handlers':  ['console'],
            'level':     'DEBUG',
            'propagate': True,
        },
    }
}
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'openid2rp.django.auth.Backend'
)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions',
    ]
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'opensubmit.contextprocessors.footer',
    'django.core.context_processors.request',    
)

JOB_EXECUTOR_SECRET = config.get("executor", "SHARED_SECRET")
assert(JOB_EXECUTOR_SECRET is not "")

GRAPPELLI_ADMIN_TITLE = "OpenSubmit"
GRAPPELLI_SWITCH_USER = True

assert(not config.has_section('overrides'))     # factored out
