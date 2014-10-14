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

# In case the backend user creates manually a SubmissionFile entry,
# we want to offer the according creation of a new submission entry.
# This is the interface or manually adding submissions


class InlineSubmissionAdmin(StackedInline):
    model = Submission
    max_num = 1
    can_delete = False


class SubmissionFileAdmin(ModelAdmin):
    list_display = ['__unicode__', 'fetched', submissions, not_withdrawn]
    inlines = [InlineSubmissionAdmin, ]

    def get_queryset(self, request):
        ''' Restrict the listed submission files for the current user.'''
        qs = super(SubmissionFileAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(submissions__assignment__course__tutors__pk=request.user.pk) | Q(submissions__assignment__course__owner=request.user)).distinct()

    def get_readonly_fields(self, request, obj=None):
        # The idea is to make some fields readonly only on modification
        # The trick is to override the getter for the according ModelAdmin attribute
        if obj:
            # Modification
            return ()
        else:
            # New manual submission
            return ('test_compile', 'test_validity', 'test_full', 'replaced_by', 'perf_data')
