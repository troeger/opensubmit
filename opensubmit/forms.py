from django import forms
from django.contrib.auth.models import User
from django.forms.models import BaseModelFormSet, modelformset_factory
from models import Submission, Assignment, SubmissionFile


class SubmissionWithGroups(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ('authors', 'notes')

    def __init__(self, current_user, ass, *args, **kwargs):
        super(SubmissionWithGroups, self).__init__(*args, **kwargs)
        # removes all users already having a submission for the assignment + the current user
        havingSubmissions = []
        for submission in ass.submissions.all().exclude(state=Submission.WITHDRAWN):
            for author in submission.authors.all():
                havingSubmissions.append(author.pk)
        self.fields['authors'].queryset = User.objects.exclude(pk__in=havingSubmissions).exclude(pk=current_user.pk)
        # since the submitter is added automatically, the number of co-authors may be zero
        self.fields['authors'].required = False


class SubmissionWithoutGroups(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ('notes',)

    def __init__(self, current_user, ass, *args, **kwargs):
        super(SubmissionWithoutGroups, self).__init__(*args, **kwargs)


class SubmissionWithoutGroupsWithFileForm(SubmissionWithoutGroups):
    attachment = forms.FileField()


class SubmissionWithoutGroupsWithoutFileForm(SubmissionWithoutGroups):
    pass


class SubmissionWithGroupsWithFileForm(SubmissionWithGroups):
    attachment = forms.FileField()


class SubmissionWithGroupsWithoutFileForm(SubmissionWithGroups):
    pass


class SubmissionFileUpdateForm(forms.ModelForm):

    attachment = forms.FileField()

    class Meta:
        model = Submission
        fields = ('notes',)



def getSubmissionForm(assignment):
    if assignment.course.max_authors > 1:
        if assignment.has_attachment:
            return SubmissionWithGroupsWithFileForm
        else:
            return SubmissionWithGroupsWithoutFileForm
    else:
        if assignment.has_attachment:
            return SubmissionWithoutGroupsWithFileForm
        else:
            return SubmissionWithoutGroupsWithoutFileForm


class SettingsForm(forms.ModelForm):
    email = forms.CharField(max_length=75, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    username = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
