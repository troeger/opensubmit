'''
    A Python Social (PSA) authentication backend.

    It performs no authentication by itself, but believes in auth information that is
    stored by a separate view in the *session*.

    This is used for performing the authentication in an independent view,
    but managing the database and user creation still in PSA.

    Since PSA really wants to do all login views by itself,
    the separate auth view needs to redirect to '/login/passthrough/'
    after storing all data in the session variable SESSION_VAR.
    The keys can be seen in get_user_details().

    After the redirect, everything works as usual in Python Social,
    with the only exception that the auth_url redirect is no longer needed.
'''

import logging
from social_core.backends.base import BaseAuth
from django.core.exceptions import PermissionDenied
from django.conf import settings

SESSION_VAR = 'passthrough_auth_data_' + settings.SECRET_KEY

logger = logging.getLogger('OpenSubmit')


class PassThroughAuth(BaseAuth):
    name = 'passthrough'

    def auth_url(self):
        """Must return redirect URL to auth provider."""
        return self.strategy.build_absolute_uri(settings.MAIN_URL + '/complete/' + self.name)

    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        if SESSION_VAR not in self.strategy.request.session:
            # This is the only protection layer when people
            # go directly to the passthrough login view.
            logger.warn("Auth data for passthrough provider not found in session. Raising 404.")
            raise PermissionDenied
        auth_data = self.strategy.request.session[SESSION_VAR]
        kwargs.update({'response': auth_data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_user_details(self, response):
        """ Complete with additional information from session, as available. """
        result = {
            'id': response['id'],
            'username': response.get('username', None),
            'email': response.get('email', None),
            'first_name': response.get('first_name', None),
            'last_name': response.get('last_name', None)
        }
        if result['first_name'] and result['last_name']:
            result['fullname'] = result['first_name'] + \
                ' ' + result['last_name']
        return result

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server response."""
        return response['id']
