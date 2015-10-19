# Course admin interface
import django.contrib.admin
from django.db.models import Q
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.utils.html import format_html

def assignments(course):
    return ",\n".join([str(ass) for ass in course.assignments.all()])

def actions(course):
    allow_tags=True
    result  = format_html('<a href="%s" style="white-space: nowrap">Download course archive</a><br/>'%reverse('coursearchive', args=(course.pk,)))
    result += format_html('<a href="%s" style="white-space: nowrap">Show grading table</a><br/>'%reverse('gradingtable', args=(course.pk,)))
    result += format_html('<a href="%s" style="white-space: nowrap">eMail to students</a>'%reverse('mail2all', args=(course.pk,)))
    return result

class CourseAdmin(django.contrib.admin.ModelAdmin):
    list_display = ['__unicode__', 'active', 'owner', assignments, 'max_authors', actions]
    filter_horizontal = ['tutors']

    def get_queryset(self, request):
        ''' Restrict the listed courses for the current user.'''
        qs = super(CourseAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(tutors__pk=request.user.pk) | Q(owner=request.user)).distinct()
