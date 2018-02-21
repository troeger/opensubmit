from django.shortcuts import redirect
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from oauthlib.oauth1 import RequestValidator
from lti.contrib.django import DjangoToolProvider
from lti import ToolConfig

from opensubmit.models import Course
from opensubmit.social import passthrough
from opensubmit import settings

import logging
logger = logging.getLogger('OpenSubmit')


class LtiRequestValidator(RequestValidator):
    dummy_client = 'NiemandWuerdeEinenDeutschenLtiKeyAnlegenDerSoLangIstAlsoEinGuterDummy'
    client_key_length = (1, 100)   # relax default restrictions

    def get_client_secret(self, client_key, request):
        '''
        Return secret for client key.

        Dummy client handling as described in
        http://oauthlib.readthedocs.io/en/latest/_modules/oauthlib/oauth1/rfc5849/request_validator.html
        '''
        if client_key == self.dummy_client:
            return self.dummy_client + 'MitSecret'
        else:
            return Course.objects.get(lti_key=client_key).lti_secret

    @property
    def enforce_ssl(self):
        if settings.DEBUG:
            # for test suite runs
            return False
        else:
            return True

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce, request, request_token=None, access_token=None):
        '''
        Allow replay attacks.
        Ok, seriousely: TODO for storing nonce in database.
        '''
        return True

    def validate_client_key(self, client_key, request):
        return Course.objects.filter(lti_key=client_key).exists()


def login(request):
    '''View to check the provided LTI credentials.

    Getting in with a faked LTI consumer basically demands a
    staff email adress and a valid LTI key / secret pair.
    Which makes the latter really security sensitive.
    '''
    post_params = request.POST
    tool_provider = DjangoToolProvider.from_django_request(request=request)
    validator = LtiRequestValidator()
    if tool_provider.is_valid_request(validator):
        data = {}
        data['ltikey'] = post_params.get('oauth_consumer_key')
        # None of them is mandatory
        data['id'] = post_params.get('user_id', None)
        data['username'] = post_params.get('custom_username', None)
        data['last_name'] = post_params.get('lis_person_name_family', None)
        data['email'] = post_params.get('lis_person_contact_email_primary', None)
        data['first_name'] = post_params.get('lis_person_name_given', None)
        request.session[passthrough.SESSION_VAR] = data # this enables the login
        return redirect(reverse('social:begin', args=['lti']))
    else:
        raise PermissionDenied


def config(request):
    launch_url = request.build_absolute_uri(reverse('lti'))

    lti_tool_config = ToolConfig(
        title='OpenSubmit',
        description='Assignment Management and Submission System',
        launch_url=launch_url,
        secure_launch_url=launch_url)

    return HttpResponse(lti_tool_config.to_xml(), content_type='text/xml')
