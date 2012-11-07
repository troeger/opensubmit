from submit.models import Grading, GradingScheme, Course, Assignment, Submission, SubmissionFile, Job
from django.contrib import admin

admin.site.register(Grading)
admin.site.register(GradingScheme)
admin.site.register(Course)
admin.site.register(Assignment)
admin.site.register(Job)

class SubmissionFileInline(admin.TabularInline):
	model = SubmissionFile

def number_of_files(submission):
	return submission.files.count()

def authors(submission):
    return "\n".join([author.get_full_name() for author in submission.authors.all()])

class SubmissionAdmin(admin.ModelAdmin):
	inlines = [SubmissionFileInline,]
	list_display = ['__unicode__', 'assignment', 'created', 'submitter', authors, number_of_files, 'state', 'grading']
	date_hierarchy = 'created'
	list_filter = ('state',)
admin.site.register(Submission, SubmissionAdmin)
