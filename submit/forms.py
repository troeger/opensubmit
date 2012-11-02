from django import forms
from django.contrib.auth.models import User
from models import Submission, Assignment

class SubmissionWithGroupsForm(forms.ModelForm):
	class Meta:
		model = Submission
		exclude = ('assignment', 'submitter', 'files', 'to_be_graded', 'grading')
	def removeFinishedAuthors(self, ass):
		havingSubmissions=[]
		for submission in ass.submissions.filter(to_be_graded=True).all():
			for author in submission.authors.all():
				havingSubmissions.append(author.pk)
		self.fields['authors'].queryset = User.objects.exclude(pk__in=havingSubmissions)



class SubmissionWithoutGroupsForm(forms.ModelForm):
	class Meta:
		model = Submission
		exclude = ('assignment', 'submitter', 'files', 'to_be_graded', 'grading', 'authors')
	def removeFinishedAuthors(self, ass):
		pass