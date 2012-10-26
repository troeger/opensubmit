from django import forms
from models import Submission

class SubmissionForm(forms.ModelForm):
	class Meta:
		model = Submission
		exclude = ('submitter',)
