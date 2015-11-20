# Assignment admin interface

from django.contrib.admin import ModelAdmin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from opensubmit.models import Course
from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.utils.html import format_html

class AssignmentAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        '''
            The intention here is to correct the shown download URL for already existing test script uploads,
            which is suprisingly hard.
            The URL comes as read-only field from the underlying storage system implementation, which
            generates it from the relative file path and MEDIA_URL. Since we want to control all media file downloads,
            MEDIA_URL is not given in OpenSubmit, so the resulting URL does not exist. Since test scripts are not
            a separate model as submission files (*sick*), we cannot use the elegant get_absolute_url() override to
            fix the download URL for a test script. Instead, we hack the widget rendering here.
        '''
        super(AssignmentAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:        # makes only sense if this is not a new assignment to be created
            self.fields['attachment_test_validity'].widget.template_with_initial = (
                '%(initial_text)s: <a href="'+self.instance.validity_test_url()+'">%(initial)s</a> '
                '%(clear_template)s<br />%(input_text)s: %(input)s'
            )
            self.fields['attachment_test_full'].widget.template_with_initial = (
                '%(initial_text)s: <a href="'+self.instance.full_test_url()+'">%(initial)s</a> '
                '%(clear_template)s<br />%(input_text)s: %(input)s'
            )

    def clean(self):
        '''
            Check if such an assignment configuration makes sense, and reject it otherwise.
            This mainly relates to interdependencies between the different fields, since
            single field constraints are already clatified by the Django model configuration.
        '''
        super(AssignmentAdminForm, self).clean()
        d = self.cleaned_data
        # Having compilation, validation or full test enabled demands file upload
        if d['attachment_test_compile'] and not d['has_attachment']:
            raise ValidationError('You cannot have compilation enabled without allowing file upload.')
        if d['attachment_test_validity'] and not d['has_attachment']:
            raise ValidationError('You cannot have a validation script without allowing file upload.')
        if d['attachment_test_full'] and not d['has_attachment']:
            raise ValidationError('You cannot have a full test script without allowing file upload.')
        # Having compilation, validation or full test enabled demands a test machine
        if d['attachment_test_compile'] and not len(d['test_machines'])>0:
            raise ValidationError('You cannot have compilation enabled without specifying test machines.')
        if d['attachment_test_validity'] and not len(d['test_machines'])>0:
            raise ValidationError('You cannot have a validation script without specifying test machines.')
        if d['attachment_test_full'] and not len(d['test_machines'])>0:
            raise ValidationError('You cannot have a full test script without specifying test machines.')
        # Having test machines demands compilation or validation scripts
        if len(d['test_machines'])>0               \
            and not d['attachment_test_validity']  \
            and not d['attachment_test_full']      \
            and not d['attachment_test_compile']:
            raise ValidationError('For using test machines, you need to enable compilation, validation or full test.')

def course(obj):
    ''' Course name as string.'''
    return str(obj.course)

def num_subm(obj):
    return obj.valid_submissions().count()
num_subm.short_description = "Submissions"

def num_authors(obj):
    return obj.authors().count()
num_authors.short_description = "Authors"

def num_finished(obj):
    return obj.graded_submissions().count()
num_finished.short_description = "Grading finished"

def num_unfinished(obj):
    unfinished=obj.grading_unfinished_submissions().count()
    gradable  =obj.gradable_submissions().count()
    return "%u (%u)"%(gradable, unfinished)
num_unfinished.short_description = "To be graded (unfinished)"

def perf_link(obj):
    ''' Link to performance data overview.'''
    if obj.has_perf_results():
        return format_html('<a href="%s" style="white-space: nowrap">Performance data</a>'%reverse('perftable', args=(obj.pk,)))
    else:
        return format_html('')
perf_link.short_description = ""


class AssignmentAdmin(ModelAdmin):
    list_display = ['__unicode__', course, 'soft_deadline', 'hard_deadline', num_authors, num_subm, num_finished, num_unfinished, perf_link]
    list_filter = ('course',)

    form = AssignmentAdminForm

    fieldsets = (
            ('',
                {'fields': (('title','course'), 'download', 'gradingScheme')}),
            ('Time',
                {   'fields': ('publish_at', ('soft_deadline', 'hard_deadline'))}),
            ('Submission and Validation',
                {   'fields': (('has_attachment', 'attachment_test_timeout'), 'attachment_test_compile', \
                               ('attachment_test_validity', 'validity_script_download'), \
                                'attachment_test_full'),
                }),
            ('Test Machines',
                {'fields': ('test_machines',)}),
    )

    def get_queryset(self, request):
        ''' Restrict the listed assignments for the current user.'''
        qs = super(AssignmentAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(course__tutors__pk=request.user.pk) | Q(course__owner=request.user)).distinct()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(active=True)
        return super(AssignmentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)