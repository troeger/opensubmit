from __future__ import print_function

import sys
import os
from ConfigParser import SafeConfigParser


# The following section determines which configuration file to load.
# It also deduces whether we are in a live environment (is_production,
# which forces DEBUG to False), or in a development environment (al-
# lowing DEBUG mode).
#
# The application first searches for files named 'settings.ini' in
# either the system's configuration directory (%APPDATA% on Windows,
# /etc on others) or in the directory where the settings.py is located.
# If this file is found, it is loaded in is_production mode (no DEBUG).
# Then, same behaviour applies for a 'settings_dev.ini' file, which
# starts the app in the DEBUG mode specified in the configuration file.
#
# If both these files cannot be found, the template file located in
# the settings.py directory, called 'settings.ini.template', is loaded
# in DEBUG mode.
def find_config_info():
    config_info_default = (os.path.abspath('submit/settings.ini.template'), False, )

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
        os.path.join(system_config_directory, 'submit'),
        os.path.join(os.path.dirname(__file__)),
    ]

    config_files = (
        ('settings.ini', True, ),
        ('settings_dev.ini', False, ),
    )

    for config_file, production in config_files:
        for config_path in config_directories:
            config_file_path = os.path.join(config_path, config_file)
            if os.path.isfile(config_file_path):
                return (config_file_path, production, )

    print("No configuration file found. Please copy .../submit/settings.ini.template to {} and edit it. Falling back to default settings.".format(os.path.join(config_directories[0], config_files[0][0])), file=sys.stderr)
    print("WARNING: THIS APP IS EXECUTED IN DEBUG MODE.", file=sys.stderr)
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
SECRET_KEY = config.get("server", "SECRET_KEY")
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
    'submit/templates/',
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
    'rest_framework',

    'submit',
    'executor_api',
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
        'Submit': {
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
    'submit.contextprocessors.footer'
)

JOB_EXECUTOR_SECRET = config.get("executor", "SHARED_SECRET")
assert(JOB_EXECUTOR_SECRET is not "")

# If config file has a section 'overrides',
# override global config variables.
if config.has_section('overrides'):
    global_vars = globals()
    for key, value in config.items('overrides'):
        key = key.upper().strip()
        if key.endswith('[]'):
            key = key[:-2].strip()
            values = map(lambda s: s.strip(), value.split(","))
            if key in global_vars:
                value_type = type(global_vars[key])
                global_vars[key] = value_type(global_vars[key] + value_type(values))
                del value_type
            else:
                global_vars[key] = tuple(values)
            del values
        else:
            value = value.strip()
            global_vars[key] = value
        del key, value
    del global_vars
