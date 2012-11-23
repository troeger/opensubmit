from submit.models import Grading, GradingScheme, Course, Assignment, Submission, SubmissionFile
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
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
	return "\n".join([author.get_full_name() for author in submission.authors.all()])

def course(submission):
	return submission.assignment.course

class SubmissionAdmin(admin.ModelAdmin):	
	list_display = ['__unicode__', course, 'assignment', authors, 'state']
	list_filter = (SubmissionStateFilter,'assignment')
	filter_horizontal = ('authors',)
	readonly_fields = ('assignment','submitter','authors','notes')
	fields = ('assignment','submitter','authors','notes','state','grading','grading_notes')
#	def formfield_for_foreignkey(self, db_field, request, **kwargs):
#		if db_field.name == "file_upload":
#			kwargs["readonly"] = False
#		return super(SubmissionAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
	def formfield_for_choice_field(self, db_field, request, **kwargs):
		if db_field.name == "state":
			kwargs['choices'] = (
				(Submission.GRADED_PASS, 'Graded - Passed'),
				(Submission.GRADED_FAIL, 'Graded - Failed'),
				(Submission.TEST_FULL_PENDING, 'Restart full test')				
			)
		return super(SubmissionAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

admin.site.register(Submission, SubmissionAdmin)
