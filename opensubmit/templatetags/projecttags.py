from django import template
from django.template.defaultfilters import stringfilter
import os
import opensubmit

register = template.Library()

@register.filter(name='basename')
@stringfilter
def basename(value):
    return os.path.basename(value)

@register.simple_tag
def setting(name):
    return getattr(opensubmit.settings, name, "")
