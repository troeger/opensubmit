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

DEBUG = bool(config.get('general', 'DEBUG')) and not is_production
TEMPLATE_DEBUG = DEBUG

# Let the user specify the complete URL, and split it up accordingly
# FORCE_SCRIPT_NAME is needed for handling subdirs accordingly on Apache
MAIN_URL = config.get('server', 'HOST') + config.get('server', 'HOST_DIR')
url = MAIN_URL.split('/')
FORCE_SCRIPT_NAME = config.get('server', 'HOST_DIR')

LOGIN_URL = MAIN_URL
LOGIN_ERROR_URL = MAIN_URL
LOGIN_REDIRECT_URL = MAIN_URL+'/dashboard/'

MEDIA_ROOT = config.get('server', 'MEDIA_ROOT')
MEDIA_URL = MAIN_URL + '/files/'

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))+os.sep

if is_production:
    STATIC_ROOT = SCRIPT_ROOT + 'static-production/'
    STATIC_URL = MAIN_URL + '/static/'
    STATICFILES_DIRS = (SCRIPT_ROOT + 'static/', )
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    ALLOWED_HOSTS = [MAIN_URL.split('/')[2]]
    SERVER_EMAIL = config.get('admin', 'ADMIN_EMAIL')
else:
    STATIC_ROOT = 'static/'
    STATIC_URL = '/static/'
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    ALLOWED_HOSTS = ['localhost']

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
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware'
)
ROOT_URLCONF = 'opensubmit.urls'
WSGI_APPLICATION = 'opensubmit.wsgi.application'
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin.apps.SimpleAdminConfig',
    'social.apps.django_app.default',
    'bootstrapform',
    'grappelli',
    'opensubmit',
)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
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
            'filters': ['require_debug_true'],
            'class':   'logging.StreamHandler'
        },
	'file': {
	    'level':   'DEBUG',
	    'class':   'logging.FileHandler',
	    'filename':   '/tmp/opensubmit.log'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'OpenSubmit': {
            'handlers':  ['console', 'file'],
            'level':     'DEBUG',
            'propagate': True,
        },
        'social': {
            'handlers':  ['console', 'file'],
            'level':     'DEBUG',
            'propagate': True,
        },
    }
}

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
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect'
)

LOGIN_GOOGLE =  config.getboolean('login', 'LOGIN_GOOGLE')
LOGIN_OPENID =  config.getboolean('login', 'LOGIN_OPENID')
LOGIN_GITHUB =  config.getboolean('login', 'LOGIN_GITHUB')
LOGIN_TWITTER = config.getboolean('login', 'LOGIN_TWITTER')
LOGIN_SHIB = config.getboolean('login', 'LOGIN_SHIB')

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

if LOGIN_GOOGLE:
    AUTHENTICATION_BACKENDS += ('social.backends.google.GoogleOAuth2',)
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY =    config.get("login", "LOGIN_GOOGLE_OAUTH_KEY")
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config.get("login", "LOGIN_GOOGLE_OAUTH_SECRET")

if LOGIN_TWITTER:
    AUTHENTICATION_BACKENDS += ('social.backends.twitter.TwitterOAuth',)
    SOCIAL_AUTH_TWITTER_KEY =          config.get("login", "LOGIN_TWITTER_OAUTH_KEY")
    SOCIAL_AUTH_TWITTER_SECRET =       config.get("login", "LOGIN_TWITTER_OAUTH_SECRET")

if LOGIN_GITHUB:
    AUTHENTICATION_BACKENDS += ('social.backends.github.GithubOAuth2',)
    SOCIAL_AUTH_GITHUB_KEY =           config.get("login", "LOGIN_GITHUB_OAUTH_KEY")
    SOCIAL_AUTH_GITHUB_SECRET =        config.get("login", "LOGIN_GITHUB_OAUTH_SECRET")

if LOGIN_OPENID:
    AUTHENTICATION_BACKENDS += ('opensubmit.social.open_id.OpenIdAuth',)
    LOGIN_DESCRIPTION = config.get('login', 'LOGIN_DESCRIPTION')
    OPENID_PROVIDER = config.get('login', 'OPENID_PROVIDER')

if LOGIN_SHIB:
    AUTHENTICATION_BACKENDS += ('opensubmit.social.apache.ModShibAuth',)
    LOGIN_SHIB_DESCRIPTION = config.get('login', 'LOGIN_SHIB_DESCRIPTION')

SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ['next',]
SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.social_auth.associate_by_email',  # Transition for existing users
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details'
)

JOB_EXECUTOR_SECRET = config.get("executor", "SHARED_SECRET")
assert(JOB_EXECUTOR_SECRET is not "")

GRAPPELLI_ADMIN_TITLE = "OpenSubmit"
GRAPPELLI_SWITCH_USER = True

assert(not config.has_section('overrides'))     # factored out
