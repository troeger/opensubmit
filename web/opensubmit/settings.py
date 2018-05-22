import os
from configparser import SafeConfigParser

from django.core.exceptions import ImproperlyConfigured

script_dir = os.path.dirname(__file__)
VERSION = '0.7.8'

NOT_CONFIGURED_VALUE = '***not configured***'


class Config():
    config_file = None
    config = None
    is_production = None

    def __init__(self, config_files):
        '''
        Creates a new config object.

        Parameters:
        config_files: Dictionary with file_name: is_production setting
        '''
        for config_file, is_production in config_files:
            if os.path.isfile(config_file):
                self.config_file = config_file
                self.is_production = is_production
                self.config = SafeConfigParser()
                self.config.read([self.config_file], encoding='utf-8')
                return

        raise IOError("No configuration file found.")

    def has_option(self, name, category):
        return self.config.has_option(name, category)

    def get_bool(self, name, category, default):
        if not self.has_option(name, category):
            return default
        text = self.get(name, category)
        return text.lower() in ['true', 't', 'yes', 'active', 'enabled']

    def get(self, name, category, mandatory=False, expect_leading_slash=None, expect_trailing_slash=None):
        text = self.config.get(name, category)
        logtext = "Setting '[%s] %s' in %s has the value '%s'" % (category, name, self.config_file, text)

        if mandatory and text == NOT_CONFIGURED_VALUE:
            raise ImproperlyConfigured(logtext + ', but must be set.')

        if len(text) == 0:
            if expect_leading_slash or expect_trailing_slash:
                raise ImproperlyConfigured(logtext + ", but should not be empty.")
        else:
            if not text[0] == '/' and expect_leading_slash is True:
                raise ImproperlyConfigured(logtext + ", but should have a leading slash.")
            if not text[-1] == '/' and expect_trailing_slash is True:
                raise ImproperlyConfigured(logtext + ", but should have a trailing slash.")
            if text[0] == '/' and expect_leading_slash is False:
                raise ImproperlyConfigured(logtext + ", but shouldn't have a leading slash.")
            if text[-1] == '/' and expect_trailing_slash is False:
                raise ImproperlyConfigured(logtext + ", but shouldn't have a trailing slash.")
        return text


# Precedence rules are as follows:
# - Developer configuration overrides production configuration on developer machine.
# - Linux production system are more likely to happen than Windows developer machines.
config = Config((
    ('/etc/opensubmit/settings.ini', True),  # Linux production system
    (os.path.dirname(__file__) + '/settings_dev.ini', False),  # Linux / Mac development system
    (os.path.expandvars('$APPDATA') + 'opensubmit/settings.ini', False),  # Windows development system
    ))

################################################################################################################
################################################################################################################
################################################################################################################

# Global settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + config.get('database', 'DATABASE_ENGINE'),
        'NAME': config.get('database', 'DATABASE_NAME', True),
        'USER': config.get('database', 'DATABASE_USER'),
        'PASSWORD': config.get('database', 'DATABASE_PASSWORD'),
        'HOST': config.get('database', 'DATABASE_HOST'),
        'PORT': config.get('database', 'DATABASE_PORT'),
    }
}

# We have the is_production indicator from above, which could also determine this value.
# But sometimes, you need Django stack traces in your production system for debugging.
DEBUG = config.get_bool('general', 'DEBUG', default=False)

# Demo mode allows login bypass
DEMO = config.get_bool('general', 'DEMO', default=False)

# Determine MAIN_URL / FORCE_SCRIPT option
HOST = config.get('server', 'HOST')
HOST_DIR = config.get('server', 'HOST_DIR')
if len(HOST_DIR) > 0:
    MAIN_URL = HOST + '/' + HOST_DIR
    FORCE_SCRIPT_NAME = '/' + HOST_DIR
else:
    MAIN_URL = HOST
    FORCE_SCRIPT_NAME = ''

# Determine some settings based on the MAIN_URL
LOGIN_URL = MAIN_URL
LOGIN_ERROR_URL = MAIN_URL
LOGIN_REDIRECT_URL = MAIN_URL + '/dashboard/'

# Local file system storage for uploads.
# Please note that MEDIA_URL is intentionally not set, since all media
# downloads have to use our download API URL for checking permissions.
MEDIA_ROOT = config.get('server', 'MEDIA_ROOT', True, True, True)

# Root of the installation
# This is normally detected automatically, so the settings.ini template does
# not contain the value. For the test suite, however, we need the override option.
if config.has_option('general', 'SCRIPT_ROOT'):
    SCRIPT_ROOT = config.get('general', 'SCRIPT_ROOT', True, True, False)
else:
    SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Determine list of allowed hosts
host_list = [MAIN_URL.split('/')[2]]
if ':' in host_list[0]:
    # Strip port number
    host_list = [host_list[0].split(':')[0]]
if config.has_option('server', 'HOST_ALIASES'):
    add_hosts = config.get('server', 'HOST_ALIASES', True, False, False).split(',')
    host_list += add_hosts
ALLOWED_HOSTS = host_list

if config.is_production:
    # Root folder for static files
    STATIC_ROOT = SCRIPT_ROOT + '/static-production/'
    STATICFILES_DIRS = (SCRIPT_ROOT + '/static/', )
    # Absolute URL for static files, directly served by Apache on production systems
    STATIC_URL = MAIN_URL + '/static/'
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    SERVER_EMAIL = config.get('admin', 'ADMIN_EMAIL')
else:
    # Root folder for static files
    STATIC_ROOT = SCRIPT_ROOT + '/static/'
    # Relative URL for static files
    STATIC_URL = '/static/'
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# OpenSubmit information
ADMIN_NAME = config.get('admin', 'ADMIN_NAME')
ADMIN_EMAIL = config.get('admin', 'ADMIN_EMAIL')
if config.has_option('admin', 'ADMIN_ADDRESS'):
    ADMIN_ADDRESS = config.get('admin', 'ADMIN_ADDRESS')
else:
    ADMIN_ADDRESS = "(Address available on request.)"
# Django information
ADMINS = (
    (ADMIN_NAME, ADMIN_EMAIL),
)
MANAGERS = ADMINS

if config.has_option('admin', 'IMPRESS_PAGE'):
    IMPRESS_PAGE = config.get('admin', 'IMPRESS_PAGE')
else:
    IMPRESS_PAGE = None

if config.has_option('admin', 'PRIVACY_PAGE'):
    PRIVACY_PAGE = config.get('admin', 'PRIVACY_PAGE')
else:
    PRIVACY_PAGE = None

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
                         "social_django.context_processors.backends",
                         "social_django.context_processors.login_redirect")
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
    'social_django.middleware.SocialAuthExceptionMiddleware',
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
    'formtools',
    'social_django',
    'bootstrapform',
    'grappelli.dashboard',
    'grappelli',
    'django.contrib.admin',
#    'django.contrib.admin.apps.SimpleAdminConfig',
    'opensubmit.app.OpenSubmitConfig',
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
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
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
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': LOG_FILE
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'OpenSubmit': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'social': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

LOGIN_GOOGLE = (config.get("login", "LOGIN_GOOGLE_OAUTH_KEY").strip() != '' and
                config.get("login", "LOGIN_GOOGLE_OAUTH_SECRET").strip() != '')
LOGIN_GITHUB = (config.get("login", "LOGIN_GITHUB_OAUTH_KEY").strip() != '' and
                config.get("login", "LOGIN_GITHUB_OAUTH_SECRET").strip() != '')
LOGIN_TWITTER = (config.get("login", "LOGIN_TWITTER_OAUTH_KEY").strip() != '' and
                 config.get("login", "LOGIN_TWITTER_OAUTH_SECRET").strip() != '')
LOGIN_OPENID = (config.get('login', 'OPENID_PROVIDER').strip() != '')
LOGIN_SHIB = (config.get('login', 'LOGIN_SHIB_DESCRIPTION').strip() != '')

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

if LOGIN_GOOGLE:
    AUTHENTICATION_BACKENDS += ('social_core.backends.google.GoogleOAuth2',)
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config.get("login", "LOGIN_GOOGLE_OAUTH_KEY")
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config.get("login", "LOGIN_GOOGLE_OAUTH_SECRET")

if LOGIN_TWITTER:
    AUTHENTICATION_BACKENDS += ('social_core.backends.twitter.TwitterOAuth',)
    SOCIAL_AUTH_TWITTER_KEY = config.get("login", "LOGIN_TWITTER_OAUTH_KEY")
    SOCIAL_AUTH_TWITTER_SECRET = config.get("login", "LOGIN_TWITTER_OAUTH_SECRET")

if LOGIN_GITHUB:
    AUTHENTICATION_BACKENDS += ('social_core.backends.github.GithubOAuth2',)
    SOCIAL_AUTH_GITHUB_KEY = config.get("login", "LOGIN_GITHUB_OAUTH_KEY")
    SOCIAL_AUTH_GITHUB_SECRET = config.get("login", "LOGIN_GITHUB_OAUTH_SECRET")

if LOGIN_OPENID:
    AUTHENTICATION_BACKENDS += ('opensubmit.social.open_id.OpenIdAuth',)
    LOGIN_DESCRIPTION = config.get('login', 'LOGIN_DESCRIPTION')
    OPENID_PROVIDER = config.get('login', 'OPENID_PROVIDER')

if LOGIN_SHIB:
    AUTHENTICATION_BACKENDS += ('opensubmit.social.apache.ModShibAuth',)
    LOGIN_SHIB_DESCRIPTION = config.get('login', 'LOGIN_SHIB_DESCRIPTION')

AUTHENTICATION_BACKENDS += ('opensubmit.social.lti.LtiAuth',)

if DEMO is True:
    AUTHENTICATION_BACKENDS += ('opensubmit.social.passthrough.PassThroughAuth',)

SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ['next', ]
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',  # Transition for existing users
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'opensubmit.views.demo.assign_role'
)

JOB_EXECUTOR_SECRET = config.get("executor", "SHARED_SECRET")
assert(JOB_EXECUTOR_SECRET is not "")

GRAPPELLI_ADMIN_TITLE = "OpenSubmit"
GRAPPELLI_SWITCH_USER = True
GRAPPELLI_INDEX_DASHBOARD = {
    'opensubmit.admin.teacher_backend': 'opensubmit.dashboard.TeacherDashboard'
}
