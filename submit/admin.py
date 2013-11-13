from submit.models import tutor_courses, Grading, UserProfile, GradingScheme, Course, Assignment, Submission, SubmissionFile, inform_student, TestMachine
from django import forms
from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


### Submission admin interface ###

class SubmissionStateFilter(SimpleListFilter):
    ''' This custom filter allows to filter the submissions according to their state.
        Additionally, only submissions the user is tutor for are shown.
    '''
    title = _('Submission Status')
    parameter_name = 'statefilter'

    def lookups(self, request, model_admin):
        return (
            ('tobegraded', _('To be graded')),
            ('graded', _('Grading finished')),
        )

    def queryset(self, request, qs):
        qs=qs.filter(assignment__course__in=tutor_courses(request.user))
        if self.value() == 'tobegraded':
            return qs.filter(state__in=[Submission.GRADING_IN_PROGRESS, Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.SUBMITTED])
        elif self.value() == 'graded':
            return qs.filter(state__in=[Submission.GRADED])
        else:
            return qs

class SubmissionAssignmentFilter(SimpleListFilter):
    ''' This custom filter allows to filter the submissions according to their
        assignment. Only submissions from courses were the user is tutor are
        considered.
    '''
    title = _('Assignment')
    parameter_name = 'assignmentfilter'

    def lookups(self, request, model_admin):
        tutor_assignments = Assignment.objects.filter(course__in=tutor_courses(request.user))
        return ((ass.pk, ass.title) for ass in tutor_assignments)

    def queryset(self, request, qs):
        if self.value():
            return qs.filter(assignment__exact = self.value())
        else:
            return qs.filter(assignment__course__in = tutor_courses(request.user))

class SubmissionCourseFilter(SimpleListFilter):
    ''' This custom filter allows to filter the submissions according to 
        the course they belong to. Additionally, only submission that the
        user is a tutor for are returned in any of the filter settings.
    '''
    title = _('Course')
    parameter_name = 'coursefilter'

    def lookups(self, request, model_admin):
        return ((c.pk, c.title) for c in tutor_courses(request.user) )

    def queryset(self, request, qs):
        if self.value():
            return qs.filter(assignment__course__exact = self.value())
        else:
            return qs.filter(assignment__course__in = tutor_courses(request.user))

def authors(submission):
    return ",\n".join([author.get_full_name() for author in submission.authors.all()])

def course(obj):
    if type(obj) == Submission:
        return obj.assignment.course
    elif type(obj) == Assignment:
        return obj.course

def upload(submission):
    return submission.file_upload

def has_grading_notes(submission):
    if submission.grading_notes != None:
        return len(submission.grading_notes) > 0
    else:
        return False
has_grading_notes.boolean = True            # show nice little icon

class SubmissionFileLinkWidget(forms.Widget):
    def __init__(self, subFile):
        if subFile:
            self.subFileId = subFile.pk
        else:
            self.subFileId = None
        super(SubmissionFileLinkWidget, self).__init__()

    def value_from_datadict(self, data, files, name):
        return self.subFileId

    def render(self, name, value, attrs=None):
        try:
            sfile = SubmissionFile.objects.get(pk=self.subFileId)
            text = u'<a href="%s">%s</a><table border=1>'%(sfile.get_absolute_url(), sfile.basename())
            if sfile.test_compile:
                text += u'<tr><td colspan="2"><h3>Compilation test</h3><pre>%s</pre></td></tr>'%(sfile.test_compile)
            if sfile.test_validity:                
                text += u'<tr><td><h3>Validation test</h3><pre>%s</pre></td></tr>'%(sfile.test_validity)
            if sfile.test_full:                
                text += u'<tr><td><h3>Full test</h3><pre>%s</pre></td></tr>'%(sfile.test_full)
            if sfile.perf_data:
                text += u'<tr><td><h3>Performance data</h3><pre>%s</pre></td></tr>'%(sfile.perf_data)
            text += u'</table>'
            # TODO: This is not safe, since the script output can be influenced by students
            return mark_safe(text)
        except:
            return mark_safe(u'Nothing stored')

class SubmissionAdmin(admin.ModelAdmin):    
    ''' This is our version of the admin view for a single submission.
    '''
    list_display = ['__unicode__', 'created', 'submitter', authors, course, 'assignment', 'state', 'grading', has_grading_notes]
    list_filter = (SubmissionStateFilter, SubmissionCourseFilter, SubmissionAssignmentFilter)
    filter_horizontal = ('authors',)
    fields = ('assignment','authors',('submitter','notes'),'file_upload',('grading','grading_notes'))
    actions=['setInitialStateAction', 'setFullPendingStateAction', 'closeAndNotifyAction', 'notifyAction', 'getPerformanceResultsAction']

    def queryset(self, request):
        ''' Restrict the listed submission for the current user.'''
        qs = super(SubmissionAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(assignment__course__tutors__pk=request.user.pk) | Q(assignment__course__owner=request.user)).distinct() 

    def get_readonly_fields(self, request, obj=None):
        ''' Make some of the form fields read-only, but only if the view used to 
            modify an existing submission. Overriding the ModelAdmin getter
            is the documented way to do that.
        '''
        if obj:
            return ('assignment','submitter','authors','notes')
        else:
            # New manual submission
            return ()

    def formfield_for_dbfield(self, db_field, **kwargs):
        ''' Offer grading choices from the assignment definition as potential form
            field values for 'grading'.
            When no object is given in the form, the this is a new manual submission
        '''
	if hasattr(self, 'obj'):
		if self.obj and db_field.name == "grading":
		    kwargs['queryset'] = self.obj.assignment.gradingScheme.gradings

        return super(SubmissionAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def get_form(self, request, obj=None):
        ''' Establish our own renderer for the file upload field, and adjust some labels.
        '''
	form = super(SubmissionAdmin, self).get_form(request, obj)
	if obj:
		self.obj = obj
		form.base_fields['file_upload'].widget = SubmissionFileLinkWidget(getattr(obj, 'file_upload', ''))
		form.base_fields['file_upload'].required = False
		form.base_fields['grading_notes'].label = "Grading notes"
	else:
		self.obj = None
        return form

    def save_model(self, request, obj, form, change):
        ''' Our custom addition to the view HTML in templates/admin/submit/submission/change_form.HTML
            adds an easy radio button choice for the new state. This is meant to be for tutors.
            We need to peel this choice from the form data and set the state accordingly.
            The radio buttons have no default, so that we can keep the existing state
            if the user makes no explicit choice.
            Everything else can be managed as prepared by the framework.
        '''
        if 'newstate' in request.POST:
            if request.POST['newstate'] == 'finished':
                obj.state = Submission.GRADED
            elif request.POST['newstate'] == 'unfinished':
                obj.state = Submission.GRADING_IN_PROGRESS
        obj.save()

    def setInitialStateAction(self, request, queryset):
        for subm in queryset:
		subm.state = subm.get_initial_state()
		subm.save() 
    setInitialStateAction.short_description = "Mark as new incoming submission"

    def setFullPendingStateAction(self, request, queryset):
        # do not restart tests for withdrawn solutions, or for solutions in the middle of grading
        qs = queryset.filter(Q(state=Submission.SUBMITTED_TESTED)|Q(state=Submission.TEST_FULL_FAILED)|Q(state=Submission.CLOSED))
        numchanged = 0
        for subm in qs:
            if subm.assignment.has_full_test():
                if subm.state == Submission.CLOSED:
                    subm.state = Submission.CLOSED_TEST_FULL_PENDING
                else:
                    subm.state = Submission.TEST_FULL_PENDING
                subm.save()
                numchanged += 1
        if numchanged == 0:
            self.message_user(request, "Nothing changed, no testable submission found.")
        else:
            self.message_user(request, "Changed status of %u submissions."%numchanged)
    setFullPendingStateAction.short_description = "Restart full test without notification"

    def closeAndNotifyAction(self, request, queryset):
        ''' CLose all submissions were the tutor sayed that the grading is finished,
            and inform the student. CLosing only graded submissions is a safeguard,
            since backend users tend to checkbox-mark all submissions without thinking.
        '''
        mails=[]
        qs = queryset.filter(Q(state=Submission.GRADED))
        for subm in qs:
            inform_student(subm, Submission.CLOSED)
            mails.append(str(subm.pk))
        qs.update(state=Submission.CLOSED)      # works in bulk because inform_student never fails
        if len(mails) == 0:
            self.message_user(request, "Nothing closed, no mails sent.")
        else:
            self.message_user(request, "Mail sent for submissions: " + ",".join(mails))
    closeAndNotifyAction.short_description = "Close graded submissions + send notification"

    def getPerformanceResultsAction(self, request, queryset):
        qs = queryset.exclude(state=Submission.WITHDRAWN)   #avoid accidental addition of withdrawn solutions
        response=HttpResponse(mimetype="text/csv")
        response.write("Submission ID;Course;Assignment;Authors;Performance Data\n")
        for subm in qs:
            if subm.file_upload.perf_data != None:
                auth =  ", ".join([author.get_full_name() for author in subm.authors.all()])
                response.write("%u;%s;%s;%s;"%(subm.pk,course(subm),subm.assignment,auth ))         
                response.write(subm.file_upload.perf_data)
                response.write("\n")            
        return response
    getPerformanceResultsAction.short_description = "Download performance data as CSV"

admin.site.register(Submission, SubmissionAdmin)


### Submission File admin interface ###

def submissions(submfile):
    while submfile.replaced_by != None:
        submfile = submfile.replaced_by
    subms=submfile.submissions.all()
    return ','.join([str(sub) for sub in subms])

def not_withdrawn(submfile):
    return submfile.replaced_by == None
not_withdrawn.boolean = True

# In case the backend user creates manually a SubmissionFile entry,
# we want to offer the according creation of a new submission entry.
# This is the interface or manually adding submissions
class InlineSubmissionAdmin(admin.StackedInline):
    model = Submission
    max_num = 1
    can_delete = False

class SubmissionFileAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'fetched', submissions, not_withdrawn]
    inlines = [InlineSubmissionAdmin, ]

    def queryset(self, request):
        ''' Restrict the listed submission files for the current user.'''
        qs = super(SubmissionFileAdmin, self).queryset(request)
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


admin.site.register(SubmissionFile, SubmissionFileAdmin)

### Assignment admin interface ###

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', course, 'has_attachment', 'soft_deadline', 'hard_deadline', 'gradingScheme']

    def queryset(self, request):
        ''' Restrict the listed assignments for the current user.'''
        qs = super(AssignmentAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(course__tutors__pk=request.user.pk) | Q(course__owner=request.user)).distinct() 


admin.site.register(Assignment, AssignmentAdmin)

### Grading scheme admin interface ###

def gradings(gradingScheme):
    return " - ".join([str(grading) for grading in gradingScheme.gradings.all()])

def courses(gradingScheme):
    # determine the courses that use this grading scheme in one of their assignments
    course_ids = gradingScheme.assignments.all().values_list('course',flat=True)
    courses = Course.objects.filter(pk__in=course_ids)
    return ",\n".join([str(course) for course in courses])

class GradingSchemeAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', gradings, courses]

admin.site.register(Grading)
admin.site.register(GradingScheme, GradingSchemeAdmin)


### User admin interface ###
class UserProfileInline(admin.StackedInline):
    model = UserProfile

class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

### Course admin interface ###

def assignments(course):
    return ",\n".join([str(ass) for ass in course.assignments.all()])

class CourseAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'active', 'owner', assignments, 'max_authors']
    actions=['showGradingTable', 'downloadArchive']
    filter_horizontal=['tutors']

    def queryset(self, request):
        ''' Restrict the listed courses for the current user.'''
        qs = super(CourseAdmin, self).queryset(request)
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


admin.site.register(Course, CourseAdmin)

admin.site.register(TestMachine)

