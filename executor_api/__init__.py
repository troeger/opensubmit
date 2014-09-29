from django.apps import AppConfig

# Give human readable names to apps in the Django admin view
class ExecutorAPIConfig(AppConfig):
    name = 'executor_api'
    verbose_name = "Executors"

default_app_config = 'executor_api.ExecutorAPIConfig'