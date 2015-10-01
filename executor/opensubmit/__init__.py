# Disclaimer: I did not understand Python namespaces and their relation to Django apps
# Solution: Fallback if this __init__.py overwrites the one form the web project
default_app_config = 'opensubmit.app.OpenSubmitConfig'
