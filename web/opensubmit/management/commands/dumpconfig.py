from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from opensubmit.signalhandlers import check_permission_system

skiplist = ['AUTHENTICATION_BACKENDS', 'EMAIL_BACKEND', 'LOG_FILE', 
            'FORCE_SCRIPT_NAME', 'GRAPPELLI_ADMIN_TITLE', 'GRAPPELLI_INDEX_DASHBOARD',
            'GRAPPELLI_SWITCH_USER', 'INSTALLED_APPS', 'MIDDLEWARE_CLASSES', 
            'NOT_CONFIGURED_VALUE', 'ROOT_URLCONF', 'SOCIAL_AUTH_PIPELINE', 
            'SOCIAL_AUTH_URL_NAMESPACE', 'STATICFILES_FINDERS', 'TEMPLATES', 'TEST_RUNNER']


class Command(BaseCommand):
    help = 'Dumps effective configuration after config file parsing.'

    def handle(self, *args, **options):
        import opensubmit.settings as s
        for name in dir(s):
            if name is "DATABASES":
                value = getattr(s, name)
                print("DATABASE: {0}".format(value['default']))
            elif name is "LOGGING":
                value = getattr(s, name)
                print("LOGGING: {0}".format(value['handlers']))
            elif name.isupper() and name not in skiplist:
                if "SECRET" in name:
                    print("{0}: {1}".format(name, "............." + getattr(s, name)[-3:]))
                else:
                    print("{0}: {1}".format(name, getattr(s, name)))
