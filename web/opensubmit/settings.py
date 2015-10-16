from __future__ import print_function

import sys
import os
from ConfigParser import SafeConfigParser

import pkg_resources
VERSION = pkg_resources.require("opensubmit-web")[0].version

# Some helper functions

def find_config_info():
    '''
        Determine which configuration file to load.
        Returns list with path to config file and boolean flag for production system status.

        Exiting the whole application if no config file is found.
    '''
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

    print("No configuration file found. Please create settings_dev.ini or call 'opensubmit-web configure' on production systems.", file=sys.stderr)
    exit(-1)

def ensure_slash(leading, trailing, text):
    '''
        Slashes are the main source of joy in Django path and URL setups.
        Using this method in the rest of the script should make problems and expectations
        way more explicit.
        It is too early for logging here, so we need to use ugly screen outputs.
    '''
    if len(text)==0:
        if leading:
            print("'%s' should have a leading slash, but it is empty."%text)
            exit(-1)
        if trailing:
            print("'%s' should have a trailing slash, but it is empty."%text)
            exit(-1)
        return text
    if not text[0]=='/' and leading:
        print("'%s' should have a leading slash."%text)
        exit(-1)
    if not text[-1]=='/' and trailing:
        print("'%s' should have a trailing slash."%text)
        exit(-1)
    if text[0]=='/' and not leading:
        print("'%s' should have no leading slash."%text)
        exit(-1)
    if text[-1]=='/' and not trailing:
        print("'%s' should have no trailing slash."%text)
        exit(-1)
    return text

# Find configuration file and open it.
config_file_path, is_production = find_config_info()
config_fp = open(config_file_path, 'r')
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

# Set debug mode based on configuration file.
# We have the production indicator from above, which could also determine this value.
# But sometimes, you still need Django stack traces in your production system, so we ignore it here.
# Yes, this is a security problem. Get over it and believe in your admins.
DEBUG = bool(config.get('general', 'DEBUG'))
TEMPLATE_DEBUG = DEBUG

# Determine MAIN_URL / FORCE_SCRIPT option
HOST =     ensure_slash(False, False, config.get('server', 'HOST'))
HOST_DIR = ensure_slash(False, False, config.get('server', 'HOST_DIR'))
if len(HOST_DIR) > 0:
    MAIN_URL = ensure_slash(False, False, HOST + '/' + HOST_DIR)
    FORCE_SCRIPT_NAME = ensure_slash(True, False, '/'+HOST_DIR)
else:
    MAIN_URL = ensure_slash(False, False, HOST)
    FORCE_SCRIPT_NAME = ensure_slash(False, False, '')

# Determine some settings based on the MAIN_URL
LOGIN_URL = MAIN_URL
LOGIN_ERROR_URL = MAIN_URL

# Determine some settings based on the MAIN_URL
LOGIN_REDIRECT_URL = ensure_slash(False, True, MAIN_URL+'/dashboard/')

# Local file system storage for uploads
MEDIA_ROOT = ensure_slash(True, True, config.get('server', 'MEDIA_ROOT'))

# URL for the file uploads, directly served by Apache on production systems
MEDIA_URL_RELATIVE = ensure_slash(True, True, '/files/')
MEDIA_URL = ensure_slash(False, True, MAIN_URL + MEDIA_URL_RELATIVE)

# Root of the installation
SCRIPT_ROOT = ensure_slash(True, False, os.path.dirname(os.path.abspath(__file__)))

LOG_FILE = config.get('server', 'LOG_FILE')

if is_production:
    # Root folder for static files
    STATIC_ROOT = ensure_slash(True, True, SCRIPT_ROOT + '/static-production/')
    STATICFILES_DIRS = (SCRIPT_ROOT + '/static/', )
    # Absolute URL for static files, directly served by Apache on production systems
    STATIC_URL = ensure_slash(False, True, MAIN_URL + '/static/')
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    ALLOWED_HOSTS = [MAIN_URL.split('/')[2]]
    SERVER_EMAIL = config.get('admin', 'ADMIN_EMAIL')
else:
    # Root folder for static files
    STATIC_ROOT = ensure_slash(False, True, 'static/')
    # Realtive URL for static files
    STATIC_URL = ensure_slash(True, True,'/static/')
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
	    'filename':   LOG_FILE
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
