'''
    A Python Social (PSA) authentication backend.

    It performs no authentication by itself, but believes in auth information that is stored by a separate view in the session.

    This is used for performing the authentication in an independent view, but managing the database and user creation still in PSA.

    Since PSA really wants to do all login views by itself, the separate auth view needs to redirect to '/login/passthrough/'
    after storing all data in the session dict variable 'passthroughauth'. The keys can be seen in get_user_details().

    After the redirect, everything works as usual in Python Social, with the only exception that the auth_url redirect is no longer needed.
'''

from social.backends.base import BaseAuth

SESSION_VAR='passthroughauth'

class PassThroughAuth(BaseAuth):
    name='passthrough'

    def auth_url(self):
        """Must return redirect URL to auth provider."""
        return '/complete/%s/'%self.name

    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        response = self.strategy.request.session[SESSION_VAR]
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_user_details(self, response):
        """ Complete with additional information from environment, as available. """
        result = {
            'id': response['id'],
            'username': response.get('username', None),
            'email': response.get('email', None),
            'first_name': response.get('first_name', None),
            'last_name': response.get('last_name', None)
        }
        if result['first_name'] and result['last_name']:
            result['fullname']=result['first_name']+' '+result['last_name']
        return result

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server response."""
        return response['id']
