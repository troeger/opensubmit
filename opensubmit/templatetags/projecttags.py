from django import template
from django.template.defaultfilters import stringfilter
from opensubmit.models import Submission
import os
import opensubmit

register = template.Library()

@register.filter(name='basename')
@stringfilter
def basename(value):
    return os.path.basename(value)

@register.filter(name='state_label_css')
@stringfilter
def state_label_css(subm_id):
    subm = Submission.objects.get(pk=int(subm_id))
    green_label = "label label-success"
    red_label = "label label-important"
    grey_label = "label label-info"
    # We expect a submission as input
    print subm
    if subm.is_closed() and subm.grading:
        if subm.grading.means_passed:
            return green_label
        else:
            return red_label
    if subm.state in [subm.SUBMITTED_TESTED, subm.SUBMITTED, subm.TEST_FULL_PENDING, subm.GRADED, subm.TEST_FULL_FAILED]:
        return green_label
    if subm.state in [subm.TEST_COMPILE_FAILED, subm.TEST_VALIDITY_FAILED]:
        return red_label
    return grey_label

@register.simple_tag
def setting(name):
    return getattr(opensubmit.settings, name, "")
