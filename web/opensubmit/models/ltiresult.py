from django.db import models
from django.contrib.auth.models import User
from .assignment import Assignment


class LtiResult(models.Model):
    '''
    Storage for LTI parameters being used on result sending to the LMS.
    See https://www.imsglobal.org/specs/ltiomv1p0/specification for data validity
    and lifetime issues.
    '''
    user = models.ForeignKey(User, related_name='ltiresults')
    assignment = models.ForeignKey(Assignment, related_name='ltiresults')
    lis_outcome_service_url = models.URLField()
    lis_result_sourcedid = models.CharField(max_length=255)
