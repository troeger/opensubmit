from django import forms
from models import Submission, Assignment

class SubmissionForm(forms.ModelForm):
	assignment = forms.ModelChoiceField(queryset=Assignment.open_ones)
	class Meta:
		model = Submission
		exclude = ('submitter','files', 'withdrawn')
