from django import forms
from django.contrib.auth.models import User
from .models import Submission, StudyProgram


def validate_authors(authors, assignment):
    if assignment.max_authors < len(authors):
        raise forms.ValidationError(
            "At most {0} authors are allowed.".format(assignment.max_authors))
    for author in authors:
        if not assignment.can_create_submission(author):
            raise forms.ValidationError(
                "{0} is not allowed to submit solutions for this assignment.".format(author))


class SubmissionWithGroups(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ('authors', 'notes')

    def __init__(self, current_user, ass, *args, **kwargs):
        '''
        Adjusts the list of choices for the authors.'''
        super(SubmissionWithGroups, self).__init__(*args, **kwargs)

        self.assignment = ass

        # remove all users already having a submission for the assignment
        # + the current user
        havingSubmissions = []
        for submission in ass.submissions.all().exclude(state=Submission.WITHDRAWN):
            for author in submission.authors.all():
                havingSubmissions.append(author.pk)
        # The submitter should still be in the list (see #13),
        # but the course owner should not (see #56)
        allowed_authors = User.objects.exclude(
            pk__in=havingSubmissions).exclude(is_active=False)
        # But the course owner must be in the list when creating
        # a test submission (see #203)
        if current_user.pk != ass.course.owner.pk:
            allowed_authors = allowed_authors.exclude(pk=ass.course.owner.pk)
        self.fields['authors'].queryset = allowed_authors

    def clean_authors(self):
        data = self.cleaned_data['authors']
        validate_authors(data, self.assignment)
        return data


class SubmissionWithoutGroups(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ('notes',)

    def __init__(self, current_user, ass, *args, **kwargs):
        super(SubmissionWithoutGroups, self).__init__(*args, **kwargs)

        self.assignment = ass

    def clean_authors(self):
        data = self.cleaned_data['authors']
        validate_authors(data, self.assignment)
        return data


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
    if assignment.max_authors > 1:
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
    student_id = forms.CharField(
        max_length=30, required=False, label="Student ID (optional)")
    study_program = forms.ModelChoiceField(
        queryset=StudyProgram.objects, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        self.instance.profile.student_id = self.cleaned_data['student_id']
        self.instance.profile.study_program = self.cleaned_data['study_program']
        self.instance.profile.save()
        return super(SettingsForm, self).save(commit=commit)

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        self.initial['student_id'] = self.instance.profile.student_id
        self.initial['study_program'] = self.instance.profile.study_program

    def clean_study_program(self):
        data = self.cleaned_data['study_program']
        if data is None and self.instance.profile.study_program is None and StudyProgram.objects.count() > 1:
                raise forms.ValidationError(
                    "Please select your study program.")
        return data


class MailForm(forms.Form):
    subject = forms.CharField(max_length=50, required=True)
    message = forms.CharField(
        widget=forms.Textarea, required=True, initial="Dear #FIRSTNAME# #LASTNAME#, ")

