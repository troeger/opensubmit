from django import forms
from django.contrib.auth.models import User
from django.forms.models import BaseModelFormSet, modelformset_factory
from models import Submission, Assignment, SubmissionFile

class SubmissionWithGroupsForm(forms.ModelForm):
	class Meta:
		model = Submission
		fields = ('authors', 'notes')
	def removeUnwantedAuthors(self, current_user, ass):
		# removes all users already having a submission for the assignment + the current user
		havingSubmissions=[]
		for submission in ass.submissions.all().exclude(state=Submission.WITHDRAWN):
			for author in submission.authors.all():
				havingSubmissions.append(author.pk)
		self.fields['authors'].queryset = User.objects.exclude(pk__in=havingSubmissions).exclude(pk=current_user.pk)

class SubmissionWithoutGroupsForm(forms.ModelForm):
	class Meta:
		model = Submission
		fields = ('notes',)
	def removeUnwantedAuthors(self, current_user, ass):
		# there is no choice for authors in this form
		pass

class SubmissionFilesModelFormSet(BaseModelFormSet):
	def clean(self):
		super(SubmissionFilesModelFormSet, self).clean()
		for formdata in self.cleaned_data:
			if 'attachment' in formdata:
				return
		# ok, no attachment found, is this a problem ?        		
		if self.mandatory:
			raise forms.ValidationError("Please choose a file.")        	

def getSubmissionFilesFormset(assignment):
	fs=modelformset_factory(SubmissionFile, formset=SubmissionFilesModelFormSet, exclude=('submission', 'fetched', 'output', 'error_code', 'replaced_by'))
	# mark form set so that mandatory atttachments are detected on validation
	fs.mandatory = assignment.has_attachment
	return fs

class SettingsForm(forms.ModelForm):
	email = forms.CharField(max_length=75, required=True)
	first_name = forms.CharField(max_length=30, required=True)
	last_name = forms.CharField(max_length=30, required=True)
	username = forms.CharField(max_length=30, required=True)
	class Meta:
		model = User
		fields = ('username','first_name','last_name','email')
