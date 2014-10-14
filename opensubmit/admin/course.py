# Course admin interface
import django.contrib.admin
from django.db.models import Q
from django.shortcuts import redirect

def assignments(course):
    return ",\n".join([str(ass) for ass in course.assignments.all()])


class CourseAdmin(django.contrib.admin.ModelAdmin):
    list_display = ['__unicode__', 'active', 'owner', assignments, 'max_authors']
    actions = ['showGradingTable', 'downloadArchive']
    filter_horizontal = ['tutors']

    def get_queryset(self, request):
        ''' Restrict the listed courses for the current user.'''
        qs = super(CourseAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(tutors__pk=request.user.pk) | Q(owner=request.user)).distinct()

    def showGradingTable(self, request, queryset):
        course = queryset.all()[0]
        return redirect('gradingtable', course_id=course.pk)
    showGradingTable.short_description = "Show grading table"

    def downloadArchive(self, request, queryset):
        course = queryset.all()[0]
        return redirect('coursearchive', course_id=course.pk)
    downloadArchive.short_description = "Download course archive file"
