# Assignment admin interface

from django.contrib.admin import ModelAdmin
from django.db.models import Q
from opensubmit.models import Course
from django import forms
from django.core.exceptions import ValidationError

def course(obj):
	''' Course name as string.'''
	return str(obj.course)

class AssignmentAdminForm(forms.ModelForm):
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

class AssignmentAdmin(ModelAdmin):
    list_display = ['__unicode__', course, 'has_attachment', 'soft_deadline', 'hard_deadline', 'gradingScheme']

    form = AssignmentAdminForm

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