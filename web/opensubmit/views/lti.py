from django.shortcuts import redirect, get_object_or_404, render
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.views.generic.edit import UpdateView
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from oauthlib.oauth1 import RequestValidator
from lti.contrib.django import DjangoToolProvider
from lti import ToolConfig

from opensubmit.social import lti
from django.conf import settings
from opensubmit.models import Assignment, LtiResult, Submission
from opensubmit.forms import getSubmissionForm
from opensubmit.views.frontend import SubmissionNewView, SubmissionWithdrawView

import sys
import logging
logger = logging.getLogger('OpenSubmit')

# Enable OAuth console logging for debugging purposes
oauth_log = logging.getLogger('oauthlib')
oauth_log.addHandler(logging.StreamHandler(sys.stdout))
oauth_log.setLevel(logging.DEBUG)


class LtiRequestValidator(RequestValidator):
    '''
        OAuth validator that considers Moodle and Opal LMS specifics,
        and relates the auth session to a particular course and its
        LTI credentials

        Dummy client handling as described in
        http://oauthlib.readthedocs.io/en/latest/_modules/oauthlib/oauth1/rfc5849/request_validator.html
    '''
    dummy_client = 'NiemandWuerdeEinenDeutschenLtiKeyAnlegenDerSoLangIstAlsoEinGuterDummy'
    client_key_length = (20, 100)   # relax default restrictions
    nonce_length = (20, 100)        # relax default restrictions
    # relax default restrictions, sometimes Moodle OAuth timestamps are too long ago
    timestamp_lifetime = 5000

    def __init__(self, assignment_id):
        super().__init__()
        self.assignment = get_object_or_404(Assignment, pk=assignment_id)

    def get_client_secret(self, client_key, request):
        if client_key == self.dummy_client:
            return self.dummy_client + 'MitSecret'
        else:
            return self.assignment.course.lti_secret

    @property
    def enforce_ssl(self):
        if settings.DEBUG:
            # for test suite runs
            return False
        else:
            return True

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce, request, request_token=None, access_token=None):
        # TODO: Store nonces in the database and take replay attacks seriously.
        return True

    def validate_client_key(self, client_key, request):
        return self.assignment.course.lti_key == client_key


def store_report_link(backend, user, response, *args, **kwargs):
    '''
    Part of the Python Social Auth Pipeline.
    Stores the result service URL reported by the LMS / LTI tool consumer so that we can use it later.
    '''
    if backend.name is 'lti':
        assignment_pk = response.get('assignment_pk', None)
        assignment = get_object_or_404(Assignment, pk=assignment_pk)
        lti_result, created = LtiResult.objects.get_or_create(assignment=assignment, user=user)
        if created:
            logger.debug("LTI result record not found, creating it.")
        else:
            logger.debug("LTI result record found, updating it.")   # Expected, check LTI standard
        lti_result.lis_result_sourcedid = response.get('lis_result_sourcedid')
        lti_result.lis_outcome_service_url = response.get('lis_outcome_service_url')
        lti_result.save()


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
class DispatcherView(View):
    '''
        "LMS Tool URL" view for providing OpenSubmit assignments through LTI.
    '''

    def get(self, request, pk):
        '''
        The LTI tool consumer performs a GET request when it wants to fetch the tool configuration.
        We create one LTI tool per assignment, which may sound strange. The reason is that the
        natural method of treating OpenSubmit as LTI tool, and giving a choice of assignments to the
        LTI tool consumer Moodle, works in theory form the protocol viewpoint, but not in Moodle
        correctly (TODO: Reference to according Moodle issue).
        '''
        launch_url = request.build_absolute_uri(
            reverse('lti', args=[pk]))
        assignment = get_object_or_404(Assignment, pk=pk)

        lti_tool_config = ToolConfig(
            title=assignment.title,
            launch_url=launch_url,
            secure_launch_url=launch_url)

        return HttpResponse(lti_tool_config.to_xml(), content_type='text/xml')

    def post(self, request, pk):
        '''
        The LTI tool provider uses POST to send a real, OAuth-signed, request for the LTI provider content.
        '''
        logger.debug("Incoming POST request through LTI")
        tool_provider = DjangoToolProvider.from_django_request(request=request)
        validator = LtiRequestValidator(pk)
        if tool_provider.is_valid_request(validator):
            logger.debug("Valid OAuth request through LTI")
            if request.user.is_authenticated:
                logger.debug("LTI consumer is already authenticated")
                return redirect(reverse('lti_submission', args=[pk]))
            else:
                logger.debug("LTI consumer needs OpenSubmit user, starting auth pipeline")
                # Store data being used by the Django Social Auth Provider for account creation
                data = request.POST.copy()
                data['assignment_pk'] = pk
                request.session[lti.SESSION_VAR] = data
                return redirect(reverse('social:begin', args=['lti']) + "?next=" + reverse('lti_submission', args=[pk]))
        else:
            logger.error("Invalid OAuth request through LTI")
            raise PermissionDenied


class WithdrawView(SubmissionWithdrawView):
    template_name = 'lti_withdraw.html'

    def get_success_url(self):
        submission = super(UpdateView, self).get_object()
        return reverse('lti_submission', args=[submission.assignment.pk])


class SubmissionView(SubmissionNewView):
    '''
    Special version of the submission dialogue for LTI
    integration.

    The POST logic is taken from the full 'new submission' view,
    everything else needs to be tailored for the LTI case.
    '''

    template_name = 'lti_new.html'
    redirect_on_success = '.'

    def dispatch(self, request, *args, **kwargs):
        self.ass = get_object_or_404(Assignment, pk=kwargs['pk'])
        self.submission = request.user.authored.all().filter(assignment=self.ass).exclude(state=Submission.WITHDRAWN)

        if self.submission:
            self.submission = self.submission[0]
            logger.debug("Found existing submission: " + str(self.submission))
        else:
            logger.debug("No submission found for this user.")
            # Check whether new submissions are allowed.
            if not self.ass.can_create_submission(user=request.user):
                logger.warn("User is not allowed to create a new submission.")
                raise PermissionDenied(
                    "You are not allowed to create a submission for this assignment")
            self.SubmissionForm = getSubmissionForm(self.ass)
        # continue with dispatching to get() / post() methods
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.submission:
            return render(request, 'lti_details.html', {'submission': self.submission})
        else:
            submissionForm = self.SubmissionForm(request.user, self.ass)
            return render(request, 'lti_new.html', {'submissionForm': submissionForm, 'assignment': self.ass})
