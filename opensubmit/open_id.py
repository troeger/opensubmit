"""
This is our adjustment to the OpenID provider from Python Social.
It does nothing more than adding the provider URL configured in our settings file.
"""

import settings
from social.backends.open_id import OpenIdAuth as OpenIdAuthBase

class OpenIdAuth(OpenIdAuthBase):
	URL = settings.OPENID_PROVIDER
