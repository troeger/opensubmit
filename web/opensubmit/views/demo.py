import uuid
from time import gmtime, strftime
from django.core.urlresolvers import reverse
from django.views.generic import RedirectView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from opensubmit import settings
from opensubmit.social import passthrough
from opensubmit.security import make_admin, make_tutor, make_owner


def assign_role(backend, user, response, *args, **kwargs):
    '''
    Part of the Python Social Auth Pipeline.
    Checks if the created demo user should be pushed into some group.
    '''
    if backend.name is 'passthrough' and settings.DEMO is True and 'role' in kwargs['request'].session[passthrough.SESSION_VAR]:
        role = kwargs['request'].session[passthrough.SESSION_VAR]['role']
        if role == 'tutor':
            make_tutor(user)
        if role == 'admin':
            make_admin(user)
        if role == 'owner':
            make_owner(user)


class LoginView(RedirectView):
    permanent = False
    pattern_name = 'dashboard'

    def get(self, request, role):
        if settings.DEMO is True:
            tstamp = strftime("%y%m%d%H%M%S", gmtime())
            data = {'id': str(uuid.uuid4()), 'role': role, 'username': 'demo' + tstamp}
            request.session[passthrough.SESSION_VAR] = data  # this enables the login
            return redirect(reverse('social:begin', args=['passthrough']))
        else:
            raise PermissionDenied
