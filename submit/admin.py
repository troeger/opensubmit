from submit.models import Grading, GradingScheme, Course, Assignment, Submission, SubmissionFile, inform_student
from django import forms
from django.db import models
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

### Submission admin interface ###

class SubmissionStateFilter(SimpleListFilter):
	title = _('submission status')
	parameter_name = 'statefilter'

	def lookups(self, request, model_admin):
		return (
			('tobegraded', _('To be graded')),
			('graded', _('Grading in progress')),
		)

	def queryset(self, request, queryset):
		if self.value() == 'tobegraded':
			return queryset.filter(state__in=[Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.SUBMITTED])
		if self.value() == 'graded':
			return queryset.filter(state__in=[Submission.GRADED])

def authors(submission):
	return ",\n".join([author.get_full_name() for author in submission.authors.all()])

def course(obj):
	if type(obj) == Submission:
		return obj.assignment.course
	elif type(obj) == Assignment:
		return obj.course

def upload(submission):
	return submission.file_upload

def student_message(submission):
	if submission.grading_notes != None:
		return len(submission.grading_notes) > 0
	else:
		return False
student_message.boolean = True			# show nice little icon

def setFullPendingStateAction(modeladmin, request, queryset):
	# do not restart tests for withdrawn solutions
	queryset.exclude(state=Submission.WITHDRAWN).update(state=Submission.TEST_FULL_PENDING)
setFullPendingStateAction.short_description = "Restart full test for selected submissions"

def closeAndNotifyAction(modeladmin, request, queryset):
	# only notify for graded solutions
	qs = queryset.filter(state=Submission.GRADED)
	for subm in qs:
		inform_student(subm, Submission.CLOSED)
	qs.update(state=Submission.CLOSED)		# works in bulk because inform_student never fails
closeAndNotifyAction.short_description = "Close and send grading notification for selected submissions"


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
			text = u'<table border=1><tr><td colspan="2"><a href="%s">%s</a></td></tr>'%(sfile.get_absolute_url(), sfile.basename())
			text += u'<tr><td colspan="2"><h3>Compilation test</h3><pre>%s</pre></td></tr>'%(sfile.test_compile)
			text += u'<tr>'
			text += u'<td><h3>Validation test</h3><pre>%s</pre></td>'%(sfile.test_validity)
			text += u'<td><h3>Full test</h3><pre>%s</pre></td>'%(sfile.test_full)
			text += u'</tr></table>'
			# TODO: This is not safe, since the script output can be influenced by students
			return mark_safe(text)
		except:
			return mark_safe(u'Nothing stored')

class SubmissionAdmin(admin.ModelAdmin):	
	list_display = ['__unicode__', 'submitter', authors, course, 'assignment', 'state', 'grading', student_message]
	list_filter = (SubmissionStateFilter,'assignment')
	filter_horizontal = ('authors',)
	readonly_fields = ('assignment','submitter','authors','notes')
	fields = ('assignment','authors',('submitter','notes'),'file_upload','state',('grading','grading_notes'))
	actions=[setFullPendingStateAction, closeAndNotifyAction]

	def formfield_for_dbfield(self, db_field, **kwargs):
		if db_field.name == "grading":
			kwargs['queryset'] = self.obj.assignment.gradingScheme.gradings
		return super(SubmissionAdmin, self).formfield_for_dbfield(db_field, **kwargs)

	def get_form(self, request, obj=None):
		self.obj = obj
		form = super(SubmissionAdmin, self).get_form(request, obj)
		form.base_fields['file_upload'].widget = SubmissionFileLinkWidget(getattr(obj, 'file_upload', ''))
		form.base_fields['file_upload'].required = False
		form.base_fields['state'].required = True
		form.base_fields['state'].label = "Decision"
		form.base_fields['grading_notes'].label = "Message for students"
		return form

admin.site.register(Submission, SubmissionAdmin)

### Assignment admin interface ###

class AssignmentAdmin(admin.ModelAdmin):
	list_display = ['__unicode__', course, 'has_attachment', 'soft_deadline', 'hard_deadline']

admin.site.register(Assignment, AssignmentAdmin)

### Grading scheme admin interface ###

def gradings(gradingScheme):
	return ", ".join([str(grading) for grading in gradingScheme.gradings.all()])

def courses(gradingScheme):
	# determine the courses that use this grading scheme in one of their assignments
	course_ids = gradingScheme.assignments.all().values_list('course',flat=True)
	courses = Course.objects.filter(pk__in=course_ids)
	return ",\n".join([str(course) for course in courses])

class GradingSchemeAdmin(admin.ModelAdmin):
	list_display = ['__unicode__', gradings, courses]

admin.site.register(Grading)
admin.site.register(GradingScheme, GradingSchemeAdmin)

### Course admin interface ###

def assignments(course):
	return ",\n".join([str(ass) for ass in course.assignments.all()])

class CourseAdmin(admin.ModelAdmin):
	list_display = ['__unicode__', 'active', 'owner', assignments, 'max_authors']

admin.site.register(Course, CourseAdmin)
