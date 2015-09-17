"""
A Python social backend that relies on Apache's mod_shib authentication.
"""

from .env import ServerEnvAuth

class ModShibAuth(ServerEnvAuth):
    name="modshib"
    ENV_USERNAME = "REMOTE_USER"
    ENV_EMAIL = "HTTP_SHIB_ORGPERSON_EMAILADDRESS"
    ENV_FIRST_NAME = "HTTP_SHIB_INETORGPERSON_GIVENNAME"
    ENV_LAST_NAME = "HTTP_SHIB_PERSON_SURNAME"

    def auth_url(self):
        """Must return redirect URL to auth provider."""
        url = "/Shibboleth.sso/Login?target="+self.redirect_uri
        return self.strategy.absolute_uri(url)

