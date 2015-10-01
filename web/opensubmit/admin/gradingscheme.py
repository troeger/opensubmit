# Grading scheme admin interface

from django.contrib.admin import ModelAdmin
from django.db.models import Q
from opensubmit.models import Course, Grading

def gradings(gradingScheme):
    ''' Determine the list of gradings in this scheme as rendered string.
        TODO: Use nice little icons instead of (p) / (f) marking.
    '''
    result = []
    for grading in gradingScheme.gradings.all():
        if grading.means_passed:
            result.append(str(grading) + " (pass)")
        else:
            result.append(str(grading) + " (fail)")
    return '  -  '.join(result)


def courses(gradingScheme):
    # determine the courses that use this grading scheme in one of their assignments
    course_ids = gradingScheme.assignments.all().values_list('course', flat=True)
    courses = Course.objects.filter(pk__in=course_ids)
    return ",\n".join([str(course) for course in courses])


class GradingSchemeAdmin(ModelAdmin):
    list_display = ['__unicode__', gradings, courses]

    def formfield_for_dbfield(self, db_field, **kwargs):
        ''' Offer only gradings that are not already used by other schemes.'''
        grad_filter = Q(schemes=None)
        if db_field.name == "gradings":
            kwargs['queryset'] = Grading.objects.filter(grad_filter).distinct()
        return super(GradingSchemeAdmin, self).formfield_for_dbfield(db_field, **kwargs)
