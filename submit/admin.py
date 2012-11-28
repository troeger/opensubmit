from submit.models import Grading, GradingScheme, Course, Assignment, Submission, SubmissionFile
from django import forms
from django.db import models
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

admin.site.register(Grading)
admin.site.register(GradingScheme)
admin.site.register(Course)
admin.site.register(Assignment)

class SubmissionStateFilter(SimpleListFilter):
	title = _('submission status')
	parameter_name = 'statefilter'

	def lookups(self, request, model_admin):
		return (
			('tobegraded', _('To be graded')),
			('graded', _('Graded')),
		)

	def queryset(self, request, queryset):
		if self.value() == 'tobegraded':
			return queryset.filter(state__in=[Submission.SUBMITTED_TESTED,Submission.SUBMITTED])
		if self.value() == 'graded':
			return queryset.filter(state__in=[Submission.GRADED_FAIL,Submission.GRADED_PASS])

def authors(submission):
	return ",\n".join([author.get_full_name() for author in submission.authors.all()])

def course(submission):
	return submission.assignment.course

def upload(submission):
	return submission.file_upload

def setFullPendingStateAction(modeladmin, request, queryset):
	queryset.update(state=Submission.TEST_FULL_PENDING)
setFullPendingStateAction.short_description = "Restart full test for selected submissions"

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
			text = u'<a href="%s">%s</a><br/><table border=1>'%(sfile.get_absolute_url(), sfile.basename())
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
	list_display = ['__unicode__', authors, course, 'assignment', 'state']
	list_filter = (SubmissionStateFilter,'assignment')
	filter_horizontal = ('authors',)
	readonly_fields = ('assignment','submitter','authors','notes')
	fields = ('assignment','authors',('submitter','notes'),'file_upload','state',('grading','grading_notes'))
	actions=[setFullPendingStateAction]
	def formfield_for_choice_field(self, db_field, request, **kwargs):
		if db_field.name == "state":
			kwargs['choices'] = (
				(Submission.GRADED_PASS, 'Graded - Passed'),
				(Submission.GRADED_FAIL, 'Graded - Failed'),
				(Submission.TEST_FULL_PENDING, 'Restart full test'),
			)
		return super(SubmissionAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)
	def get_form(self, request, obj=None):
		form = super(SubmissionAdmin, self).get_form(request, obj)
		form.base_fields['file_upload'].widget = SubmissionFileLinkWidget(getattr(obj, 'file_upload', ''))
		form.base_fields['file_upload'].required = False
		form.base_fields['state'].required = False
		form.base_fields['state'].label = "Decision"
		form.base_fields['grading_notes'].label = "Message for students"
		return form


admin.site.register(Submission, SubmissionAdmin)

