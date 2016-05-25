from django.contrib.admin import ModelAdmin, StackedInline
from django.db.models import Q
from opensubmit.models import Submission

def submissions(submfile):
    while submfile.replaced_by is not None:
        submfile = submfile.replaced_by
    subms = submfile.submissions.all()
    return ','.join([str(sub) for sub in subms])


def not_withdrawn(submfile):
    return submfile.replaced_by is None
not_withdrawn.boolean = True

class SubmissionFileAdmin(ModelAdmin):
    list_display = ['__unicode__', 'fetched', submissions, not_withdrawn]

    class Media:
        css = {'all': ('css/admin.css',)}

    def get_queryset(self, request):
        ''' Restrict the listed submission files for the current user.'''
        qs = super(SubmissionFileAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(submissions__assignment__course__tutors__pk=request.user.pk) | Q(submissions__assignment__course__owner=request.user)).distinct()
