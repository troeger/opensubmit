from django.apps import AppConfig

# Give human readable names to apps in the Django admin view
class OpenSubmitConfig(AppConfig):
    name = 'opensubmit'
    verbose_name = "Backend"

    def ready(self):
    	from . import signalhandlers
