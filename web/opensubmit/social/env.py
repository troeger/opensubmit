"""
A Python Social backend base class that uses web server environment variables for authentication.
This is intended to perform the same as Django's RemoteUser middleware, but with all
the nice Python Social add-ons in the pipeline.

This backend class expects the following configuration variables being set by a derived class:

ENV_USERNAME   - The name of the environment variable containing the authenticated user name (mandatory).
ENV_EMAIL      - The name of the environment variable containing the eMail address of the authenticated user.
ENV_FIRST_NAME - The name of the environment variable containing the First name of the authenticated user.
ENV_LAST_NAME  - The name of the environment variable containing the Last name of the authenticated user.

It also expects auth_url to be implemented by the derived class.

Note: If you are using Apache + mod_wsgi, make sure to set 'WSGIPassAuthorization On'.
"""

from social.backends.base import BaseAuth
from social.exceptions import AuthMissingParameter
import os, logging

logger = logging.getLogger('OpenSubmit')

class ServerEnvAuth(BaseAuth):
    ENV_USERNAME = None
    ENV_EMAIL = None
    ENV_FIRST_NAME = None
    ENV_LAST_NAME = None

    def auth_url(self):
        """Must return redirect URL to auth provider."""
        raise NotImplementedError()

    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        if self.ENV_USERNAME in os.environ:
            response = os.environ
        elif type(self.strategy).__name__ == "DjangoStrategy" and self.ENV_USERNAME in self.strategy.request.META:
            # Looks like the Django strategy. In this case, it might by mod_wsgi, which stores
            # authentication environment variables in request.META
            response = self.strategy.request.META
	else:
            raise AuthMissingParameter(self, "%s, found only: %s"%(self.ENV_USERNAME, str(os.environ)))
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_user_details(self, response):
        """ Complete with additional information from environment, as available. """
        result = {
            'username': response[self.ENV_USERNAME],
            'email': response.get(self.ENV_EMAIL, None),
            'first_name': response.get(self.ENV_FIRST_NAME, None),
            'last_name': response.get(self.ENV_LAST_NAME, None)
        }
        if result['first_name'] and result['last_name']:
            result['fullname']=result['first_name']+' '+result['last_name']
        logger.debug("Returning user details: "+str(result))
        return result

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server response."""
        return response[self.ENV_USERNAME]

