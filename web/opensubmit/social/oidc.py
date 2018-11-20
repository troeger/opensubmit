"""
This is our adjustment to the OpenID Connect provider from Python Social.
"""

from django.conf import settings
from social_core.backends.open_id_connect import OpenIdConnectAuth as OpenIdConnectAuthBase

class OpenIdConnectAuth(OpenIdConnectAuthBase):
	OIDC_ENDPOINT = settings.LOGIN_OIDC_ENDPOINT if settings.LOGIN_OIDC else None

	# social_core.backends_settings.open_id_connect lacks
	# the bakcend-cache lookup name :(
	name = "oidc"

	def get_key_and_secret(self):
		return settings.LOGIN_OIDC_CLIENT_ID, settings.LOGIN_OIDC_CLIENT_SECRET
