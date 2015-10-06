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
def state_label_css(subm):
    green_label = "badge label label-success"
    red_label = "badge label label-important"
    grey_label = "badge label label-info"
    # We expect a submission as input
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

@register.assignment_tag
def setting(name):
    return getattr(opensubmit.settings, name, "")

@register.inclusion_tag('inclusion_tags/details_table.html')
def details_table(submission):
    return {'submission': submission}

