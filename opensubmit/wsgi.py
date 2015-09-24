"""
WSGI config for OpenSubmit project.
"""
import sys
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opensubmit.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

