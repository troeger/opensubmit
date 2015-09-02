"""
This is our adjustment to the OpenID provider from Python Social.
It does nothing more than adding the provider URL configured in our settings file.
"""

import social, settings

class OpenIdAuth(social.backends.open_id.OpenIdAuth):
	URL = settings.OPENID_PROVIDER
