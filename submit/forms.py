from django import forms
from django.contrib.auth.models import User
from models import Submission, Assignment, SubmissionFile

class SubmissionWithGroupsForm(forms.ModelForm):
	class Meta:
		model = Submission
		fields = ('authors', 'notes')
	def removeFinishedAuthors(self, ass):
		havingSubmissions=[]
		for submission in ass.submissions.all().exclude(state=Submission.WITHDRAWN):
			for author in submission.authors.all():
				havingSubmissions.append(author.pk)
		self.fields['authors'].queryset = User.objects.exclude(pk__in=havingSubmissions)

class SubmissionWithoutGroupsForm(forms.ModelForm):
	class Meta:
		model = Submission
		fields = ('notes',)
	def removeFinishedAuthors(self, ass):
		pass

