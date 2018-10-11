'''
    LTI authentication, based on the passthrough backend.
'''

from . import passthrough
import logging
logger = logging.getLogger('OpenSubmit')

SESSION_VAR = passthrough.SESSION_VAR  # make it a class member, but still accessible from outside


class LtiAuth(passthrough.PassThroughAuth):
    name = 'lti'

    def get_user_details(self, response):
        """ Complete with additional information from original LTI POST data, as available. """
        data = {}
        # None of them is mandatory
        data['id'] = response.get('user_id', None)
        data['username'] = response.get('custom_username', None)
        if not data['username']:
            data['username'] = response.get('ext_user_username', None)
        data['last_name'] = response.get('lis_person_name_family', None)
        data['email'] = response.get(
            'lis_person_contact_email_primary', None)
        data['first_name'] = response.get('lis_person_name_given', None)
        data['fullname'] = response.get('lis_person_name_full', None)
        logger.debug("User details being used: " + str(data))
        return data

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server response."""
        return response['user_id']
