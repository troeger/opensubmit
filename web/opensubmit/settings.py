import sys
import os
from ConfigParser import SafeConfigParser

from django.core.exceptions import ImproperlyConfigured

import pkg_resources
VERSION = pkg_resources.require("opensubmit-web")[0].version

NOT_CONFIGURED_VALUE = '***not configured***'

# Some helper functions

def find_config_info():
    '''
        Determine which configuration file to load.
        Returns path to config file and boolean flag for production system status.

        Precedence rules are as follows:
        - Developer configuration overrides production configuration on developer machine.
        - Linux production system are more likely to happen than Windows developer machines.

        Throws exception if no config file is found. This terminates the application loading.
    '''
    config_info = (
        ('/etc/opensubmit/settings.ini',                            True),  # Linux production system
        (os.path.dirname(__file__)+'/settings_dev.ini',            False),  # Linux / Mac development system
        (os.path.expandvars('$APPDATA')+'opensubmit/settings.ini', False),  # Windows development system
    )

    for config_file, production in config_info:
        if os.path.isfile(config_file):
            return (config_file, production, )

    raise IOError("No configuration file found.")

def ensure_configured(text):
    '''
        Ensure that the configuration variable value does not have the default setting.
    '''
    if text == NOT_CONFIGURED_VALUE:
        raise ImproperlyConfigured("It is not configured.")
    return text

def ensure_slash(leading, trailing, text):
    '''
        Slashes are the main source of joy in Django path and URL setups.
        Using this method in the rest of the script should make problems and expectations
        way more explicit.

        The 'leading' parameter defines if a leading slash is expected.
        The 'trailing' parameter defines if a trailing slash is expected.

        It is too early for logging here, so we use the appropriate Django exception.
    '''
    text = ensure_configured(text)
    if len(text)==0:
        if leading:
            raise ImproperlyConfigured("'%s' should have a leading slash, but it is empty."%text)
        if trailing:
            raise ImproperlyConfigured("'%s' should have a trailing slash, but it is empty."%text)
        return text
    if not text[0]=='/' and leading:
        raise ImproperlyConfigured("'%s' should have a leading slash."%text)
    if not text[-1]=='/' and trailing:
        raise ImproperlyConfigured("'%s' should have a trailing slash."%text)
    if text[0]=='/' and not leading:
        raise ImproperlyConfigured("'%s' shouldn't have a leading slash."%text)
    if text[-1]=='/' and not trailing:
        raise ImproperlyConfigured("'%s' shouldn't have a trailing slash."%text)
    return text

def ensure_slash_from_config(config, leading, trailing, configvar):
    '''
        Read configuration file variable and make sure that leading and trailing slashes are correct.
        This indirection allows to add the config variable name to the exception details.
    '''
    try:
        return ensure_slash(leading, trailing, config.get(*configvar))
    except ImproperlyConfigured as e:
        # The message attribute is deprecated since Python 2.7, so this is the better way to change the text
        raise ImproperlyConfigured("The value of configuration variable %s did not pass the sanity check. %s"%(str(configvar),e.message))

# Find configuration file and open it.
config_file_path, is_production = find_config_info()
print("Using "+config_file_path)
config_fp = open(config_file_path, 'r')
config = SafeConfigParser()
config.readfp(config_fp)

# Global settings
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.' + config.get('database', 'DATABASE_ENGINE'),
        'NAME':     ensure_configured(config.get('database', 'DATABASE_NAME')),
        'USER':     config.get('database', 'DATABASE_USER'),
        'PASSWORD': config.get('database', 'DATABASE_PASSWORD'),
        'HOST':     config.get('database', 'DATABASE_HOST'),
        'PORT':     config.get('database', 'DATABASE_PORT'),
    }
}

# We have the is_production indicator from above, which could also determine this value.
# But sometimes, you need Django stack traces in your production system for debugging.
DEBUG = config.getboolean('general', 'DEBUG')

# Determine MAIN_URL / FORCE_SCRIPT option
HOST =     ensure_slash_from_config(config, False, False, ('server', 'HOST'))
HOST_DIR = ensure_slash_from_config(config, False, False, ('server', 'HOST_DIR'))
if len(HOST_DIR) > 0:
    MAIN_URL          = HOST + '/' + HOST_DIR
    FORCE_SCRIPT_NAME = '/' + HOST_DIR
else:
    MAIN_URL = HOST
    FORCE_SCRIPT_NAME = ensure_slash(False, False, '')

# Determine some settings based on the MAIN_URL
LOGIN_URL = MAIN_URL
LOGIN_ERROR_URL = MAIN_URL
LOGIN_REDIRECT_URL = ensure_slash(False, True, MAIN_URL+'/dashboard/')

# Local file system storage for uploads.
# Please note that MEDIA_URL is intentionally not set, since all media
# downloads have to use our download API URL for checking permissions.
MEDIA_ROOT = ensure_slash_from_config(config, True, True, ('server', 'MEDIA_ROOT'))

# Root of the installation
# This is normally detected automatically, so the settings.ini template does
# not contain the value. For the test suite, however, we need the override option.
if config.has_option('general', 'SCRIPT_ROOT'):
    SCRIPT_ROOT = ensure_slash(True, False,config.get('general', 'SCRIPT_ROOT'))
else:
    SCRIPT_ROOT = ensure_slash(True, False, os.path.dirname(os.path.abspath(__file__)))

if is_production:
    # Root folder for static files
    STATIC_ROOT = ensure_slash(True, True, SCRIPT_ROOT + '/static-production/')
    STATICFILES_DIRS = (SCRIPT_ROOT + '/static/', )
    # Absolute URL for static files, directly served by Apache on production systems
    STATIC_URL = ensure_slash(False, True, MAIN_URL + '/static/')
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    ALLOWED_HOSTS = [MAIN_URL.split('/')[2]]
    if ':' in ALLOWED_HOSTS[0]:
        ALLOWED_HOSTS = [ALLOWED_HOSTS[0].split(':')[0]]
    SERVER_EMAIL = config.get('admin', 'ADMIN_EMAIL')
else:
    # Root folder for static files
    STATIC_ROOT = ensure_slash(True, True, SCRIPT_ROOT+'/static/')
    # Relative URL for static files
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {'debug': DEBUG, 
                    'context_processors':
                                            ("django.contrib.auth.context_processors.auth",
                                             "django.template.context_processors.debug",
                                             "django.template.context_processors.i18n",
                                             "django.template.context_processors.media",
                                             "django.template.context_processors.static",
                                             "django.template.context_processors.tz",
                                             "django.contrib.messages.context_processors.messages",
                                             "opensubmit.contextprocessors.footer",
                                             "django.template.context_processors.request",
                                             "social.apps.django_app.context_processors.backends",
                                             "social.apps.django_app.context_processors.login_redirect"
                                            )
                    },
        'APP_DIRS': True,
    },
]

TEST_RUNNER = 'opensubmit.tests.DiscoverRunner'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware',
    'opensubmit.middleware.CourseRegister'
)
ROOT_URLCONF = 'opensubmit.urls'
WSGI_APPLICATION = 'opensubmit.wsgi.application'
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social.apps.django_app.default',
    'bootstrapform',
    'grappelli.dashboard',
    'grappelli',
    'django.contrib.admin',
#    'django.contrib.admin.apps.SimpleAdminConfig',
    'opensubmit',
)

LOG_FILE = config.get('server', 'LOG_FILE')

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
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
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
        'formatter': 'verbose',
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

AUTHENTICATION_BACKENDS += ('opensubmit.social.lti.LtiAuth',)

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
GRAPPELLI_INDEX_DASHBOARD = {
    'opensubmit.admin.teacher_backend': 'opensubmit.dashboard.TeacherDashboard',
    'opensubmit.admin.admin_backend': 'opensubmit.dashboard.AdminDashboard',
}

assert(not config.has_section('overrides'))     # factored out
