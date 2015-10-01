# Assignment admin interface

from django.contrib.admin import ModelAdmin
from django.db.models import Q
from opensubmit.models import Course

def course(obj):
	''' Course name as string.'''
	return str(obj.course)

class AssignmentAdmin(ModelAdmin):
    list_display = ['__unicode__', course, 'has_attachment', 'soft_deadline', 'hard_deadline', 'gradingScheme']

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