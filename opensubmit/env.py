"""
A Python Social backend that uses web server environment variables for authentication.
This is intended to perform the same as Django's RemoteUser middleware, but with all
the nice Python Social add-ons in the pipeline.

This backend expects the following configuration variables:

SOCIAL_AUTH_ENV_USERNAME   - The name of the environment variable containing the authenticated user name.
SOCIAL_AUTH_ENV_EMAIL      - eMail address of the authenticated user.
SOCIAL_AUTH_ENV_FIRST_NAME - First name of the authenticated user.
SOCIAL_AUTH_ENV_LAST_NAME  - Last name of the authenticated user.
"""

from social.backends.base import BaseAuth
from social.exceptions import AuthMissingParameter, WrongBackend, AuthFailed
import os

class ServerEnvAuth(BaseAuth):
    name = 'env'
    ID_KEY = 'username'
    mappings = {'username'   : 'SOCIAL_AUTH_ENV_USERNAME',
                'email'      : 'SOCIAL_AUTH_ENV_EMAIL',
                'first_name' : 'SOCIAL_AUTH_ENV_FIRST_NAME',
                'last_name'  : 'SOCIAL_AUTH_ENV_LAST_NAME'}

    def auth_url(self):
        """Must return redirect URL to auth provider, so we use the current page."""
        return self.strategy.absolute_uri(self.setting('SOCIAL_AUTH_ENV_PROVIDER'))

    def env_val(self, data_key):
        """ Helper function:
            Determine configured environment variable name for this data key,
            and fetch the value. """
        setting_name = self.mappings[data_key]
        env_var_name = self.setting(setting_name)
        if not env_var_name:
            # Missing configuration setting
            raise AuthMissingParameter(self, setting_name)
        else:
            if env_var_name not in os.environ:
                # Environment variable does not exist
                return None
            else:
                return os.environ[env_var_name]

    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        response = {}
        uid = self.env_val(self.ID_KEY)
        if not uid:
            # Web server did not store the authenticated user name in the environment
            raise AuthMissingParameter(self, "No auth information in environment: "+str(os.environ))
        response[self.ID_KEY]=uid
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_user_details(self, response):
        """ Complete with additional information from environment, as available. """
        result = {
            'username': response[self.ID_KEY],
            'email': self.env_val('email'),
            'first_name': self.env_val('first_name'),
            'last_name': self.env_val('last_name')
        }
        if result['first_name'] and result['last_name']:
            result['fullname']=result['first_name']+' '+result['last_name']
        return result

