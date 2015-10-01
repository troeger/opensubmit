from django.apps import AppConfig
from signalhandlers import *

# Give human readable names to apps in the Django admin view
class OpenSubmitConfig(AppConfig):
    name = 'opensubmit'
    verbose_name = "Teacher Backend"
