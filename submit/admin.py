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

class SubmissionAdmin(admin.ModelAdmin):
	inlines = [SubmissionFileInline,]
	list_display = ['__unicode__', 'assignment','submitter', 'created', number_of_files]
	date_hierarchy = 'created'
admin.site.register(Submission, SubmissionAdmin)
