# Assignment admin interface

from collections import defaultdict
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
            if self.instance.validity_test_url():
                self.fields['attachment_test_validity'].widget.template_with_initial = (
                    '%(initial_text)s: <a href="'+self.instance.validity_test_url()+'">%(initial)s</a> '
                    '%(clear_template)s<br />%(input_text)s: %(input)s'
                )
            else:
                self.fields['attachment_test_validity'].widget.template_with_initial = (
                    '%(initial_text)s: %(clear_template)s<br />%(input_text)s: %(input)s'
                )
            if self.instance.full_test_url():
                self.fields['attachment_test_full'].widget.template_with_initial = (
                    '%(initial_text)s: <a href="'+self.instance.full_test_url()+'">%(initial)s</a> '
                    '%(clear_template)s<br />%(input_text)s: %(input)s'
                )
            else:
                self.fields['attachment_test_full'].widget.template_with_initial = (
                    '%(initial_text)s: %(clear_template)s<br />%(input_text)s: %(input)s'
                )

    def clean(self):
        '''
            Check if such an assignment configuration makes sense, and reject it otherwise.
            This mainly relates to interdependencies between the different fields, since
            single field constraints are already clatified by the Django model configuration.
        '''
        super(AssignmentAdminForm, self).clean()
        d = defaultdict(lambda: False)
        d.update(self.cleaned_data)
        # Having compilation, validation or full test enabled demands file upload
        if d['attachment_test_compile'] and not d['has_attachment']:
            raise ValidationError('You cannot have compilation enabled without allowing file upload.')
        if d['attachment_test_validity'] and not d['has_attachment']:
            raise ValidationError('You cannot have a validation script without allowing file upload.')
        if d['attachment_test_full'] and not d['has_attachment']:
            raise ValidationError('You cannot have a full test script without allowing file upload.')
        # Having compilation, validation or full test enabled demands a test machine
        if d['attachment_test_compile'] and 'test_machines' in d and not len(d['test_machines'])>0:
            raise ValidationError('You cannot have compilation enabled without specifying test machines.')
        if d['attachment_test_validity'] and 'test_machines' in d and not len(d['test_machines'])>0:
            raise ValidationError('You cannot have a validation script without specifying test machines.')
        if d['attachment_test_full'] and 'test_machines' in d and not len(d['test_machines'])>0:
            raise ValidationError('You cannot have a full test script without specifying test machines.')
        # Having test machines demands compilation or validation scripts
        if 'test_machines' in d and len(d['test_machines'])>0               \
            and not 'attachment_test_validity' in d  \
            and not 'attachment_test_full' in d      \
            and not 'attachment_test_compile' in d:
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

def view_links(obj):
    ''' Link to performance data and duplicate overview.'''
    result=format_html('')
    if obj.has_perf_results():
        result+=format_html('<a href="%s" style="white-space: nowrap">Performance data</a><br/>'%reverse('perftable', args=(obj.pk,)))
    result+=format_html('<a href="%s" style="white-space: nowrap">Duplicate report</a>'%reverse('duplicates', args=(obj.pk,)))
    result+=format_html('<br/><a href="%s" style="white-space: nowrap">Check submissions</a>'%obj.grading_url())
    result+=format_html('<br/><a href="%s" style="white-space: nowrap">Download submissions</a>'%reverse('assarchive', args=(obj.pk,)))
    return result
view_links.short_description = ""

class AssignmentAdmin(ModelAdmin):
    list_display = ['__unicode__', course, 'soft_deadline', 'hard_deadline', num_authors, num_subm, num_finished, num_unfinished, view_links]
    list_filter = ('course',)
    change_list_template = "admin/change_list_filter_sidebar.html"

    class Media:
        css = {'all': ('css/admin.css',)}



    form = AssignmentAdminForm

    fieldsets = (
            ('',
                {'fields': (('title','course'), 'download', 'gradingScheme', 'has_attachment')}),
            ('Time',
                {   'fields': ('publish_at', ('soft_deadline', 'hard_deadline'))}),
            ('File Upload Validation',
                {   'fields': ('attachment_test_compile',  \
                               ('attachment_test_validity', 'validity_script_download'), \
                               'attachment_test_full', ('test_machines', 'attachment_test_timeout') )},
            )
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