from datetime import datetime
import json
import os

from django.views.generic import TemplateView, RedirectView, ListView, DetailView
from django.views.generic.edit import UpdateView
from django.shortcuts import redirect
from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory, model_to_dict
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from opensubmit import settings
from opensubmit.forms import SettingsForm, getSubmissionForm, SubmissionFileUpdateForm
from opensubmit.models import UserProfile, Submission, TestMachine, Course, Assignment, SubmissionFile
from opensubmit.models.userprofile import db_fixes
from opensubmit.views.helpers import BinaryDownloadMixin


class IndexView(TemplateView):
    template_name = 'index.html'

    def get(self, request):
        if request.user.is_authenticated():
            return redirect('dashboard')
        else:
            return super(IndexView, self).get(request)

class ImpressView(TemplateView):
    template_name = 'impress.html'

    def get(self, request):
        if settings.IMPRESS_PAGE:
            return redirect(settings.IMPRESS_PAGE)
        else:
            return super(ImpressView, self).get(request)

class PrivacyView(TemplateView):
    template_name = 'privacy.html'

    def get(self, request):
        if settings.PRIVACY_PAGE:
            return redirect(settings.PRIVACY_PAGE)
        else:
            return super(PrivacyView, self).get(request)


class LogoutView(LoginRequiredMixin, RedirectView):
    '''
    TODO: Not needed with Django 1.11, which has own LogoutView.
    '''
    permanent = False
    pattern_name = 'index'

    def get(self, request):
        auth.logout(request)
        return super().get(request)


class SettingsView(LoginRequiredMixin, UpdateView):
    template_name = 'settings.html'
    form_class = SettingsForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        messages.info(self.request, 'User settings saved.')
        return super().form_valid(form)

    def get_object(self, queryset=None):
        return self.request.user


class ValidityScriptView(LoginRequiredMixin, BinaryDownloadMixin, DetailView):
    model = Assignment

    def get_object(self, queryset=None):
        ass = super().get_object(queryset)
        self.f = ass.attachment_test_validity
        self.fname = self.f.name[self.f.name.rfind('/') + 1:]
        return ass


class FullScriptView(LoginRequiredMixin, BinaryDownloadMixin, DetailView):
    model = Assignment

    def get_object(self, queryset=None):
        ass = super().get_object(queryset)
        self.f = ass.attachment_test_full
        self.fname = self.f.name[self.f.name.rfind('/') + 1:]
        return ass


class CoursesView(LoginRequiredMixin, UpdateView):
    template_name = 'courses.html'
    form_class = modelform_factory(UserProfile, fields=['courses'])
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        messages.info(self.request, 'Your choice of courses was saved.')
        return super().form_valid(form)

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.request.user.profile.user_courses()
        return context


class ArchiveView(LoginRequiredMixin, ListView):
    template_name = 'archive.html'

    def get_queryset(self):
        archived = self.request.user.authored.all().exclude(assignment__course__active=False).filter(state=Submission.WITHDRAWN).order_by('-created')
        return archived


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Student submissions under validation / grading
        context['subs_in_progress'] = self.request.user.authored.all(). \
            exclude(assignment__course__active=False). \
            exclude(state=Submission.RECEIVED). \
            exclude(state=Submission.WITHDRAWN). \
            exclude(state=Submission.CLOSED). \
            exclude(state=Submission.CLOSED_TEST_FULL_PENDING). \
            order_by('-created')

        # Closed student submissions, graded ones first
        context['subs_finished'] = self.request.user.authored.all(). \
            exclude(assignment__course__active=False). \
            filter(state__in=[Submission.CLOSED, Submission.CLOSED_TEST_FULL_PENDING]). \
            order_by('-assignment__gradingScheme', '-created')

        context['machines'] = TestMachine.objects.filter(enabled=True)
        context['today'] = datetime.now()
        context['user'] = self.request.user
        return context

    def get(self, request):
        # Check and fix database on lower levels for the current user
        db_fixes(request.user)

        # LTI keys and passwords are defined per course
        # We use this here to register students automatically for
        # courses based on their LTI credentials.
        # Note: Authentication is already over here.
        if 'passthroughauth' in request.session:
            if 'ltikey' in request.session['passthroughauth']:
                try:
                    ltikey = request.session['passthroughauth']['ltikey']
                    request.session['ui_disable_logout'] = True
                    course = Course.objects.get(lti_key=ltikey)
                    request.user.profile.courses.add(course)
                    request.user.profile.save()
                except Exception:
                    # LTI-based course registration is only a comfort function,
                    # so we should not crash the app if that goes wrong
                    pass

        # This is the first view than can check
        # if the user settings are complete.
        # This depends on the amount of information the authentication provider
        # already handed in.
        # If incomplete, then we drop annyoing popups until the user gives up.
        settingsform = SettingsForm(model_to_dict(request.user), instance=request.user)
        if not settingsform.is_valid():
            msg = 'Your <a href="{0}">user settings</a> are incomplete.'.format(reverse('settings'))
            messages.error(request, mark_safe(msg))

        return super().get(request)


class SubmissionDetailsView(LoginRequiredMixin, DetailView):
    template_name = 'details.html'
    model = Submission

    def get_object(self, queryset=None):
        subm = super().get_object(queryset)
        # only authors should be able to look into submission details
        if not (self.request.user in subm.authors.all() or self.request.user.is_staff):
            raise PermissionDenied()
        return subm


class MachineDetailsView(LoginRequiredMixin, DetailView):
    template_name = 'machine.html'
    model = TestMachine

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['config'] = json.loads(self.object.config)
        except Exception:
            context['config'] = []
        context['queue'] = Submission.pending_student_tests.all()
        context['additional'] = len(Submission.pending_full_tests.all())
        return context


class SubmissionNewView(LoginRequiredMixin, TemplateView):
    '''
    TODO: Currently an ugly direct conversion of the old view
    function implementation. Using something like CreateView
    demands tailoring of the double-form setup here.
    '''
    template_name = 'new.html'

    def dispatch(self, request, *args, **kwargs):
        self.ass = get_object_or_404(Assignment, pk=kwargs['pk'])

        # Check whether submissions are allowed.
        if not self.ass.can_create_submission(user=request.user):
            raise PermissionDenied(
                "You are not allowed to create a submission for this assignment")

        # get submission form according to the assignment type
        self.SubmissionForm = getSubmissionForm(self.ass)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # we need to fill all forms here,
        # so that they can be rendered on validation errors
        submissionForm = self.SubmissionForm(request.user,
                                             self.ass,
                                             request.POST,
                                             request.FILES)
        if submissionForm.is_valid():
            # commit=False to set submitter in the instance
            submission = submissionForm.save(commit=False)
            submission.submitter = request.user
            submission.assignment = self.ass
            submission.state = submission.get_initial_state()
            # take uploaded file from extra field
            if self.ass.has_attachment:
                upload_file = request.FILES['attachment']
                submissionFile = SubmissionFile(
                    attachment=submissionForm.cleaned_data['attachment'],
                    original_filename=upload_file.name)
                submissionFile.save()
                submission.file_upload = submissionFile
            submission.save()
            # because of commit=False, we first need to add
            # the form-given authors
            submissionForm.save_m2m()
            submission.save()
            messages.info(request, "New submission saved.")
            if submission.state == Submission.SUBMITTED:
                # Initial state is SUBMITTED,
                # which means that there is no validation
                if not submission.assignment.is_graded():
                    # No validation, no grading. We are done.
                    submission.state = Submission.CLOSED
                    submission.save()
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct your submission information.")
            return render(request, 'new.html', {'submissionForm': submissionForm, 'assignment': self.ass})

    def get(self, request, *args, **kwargs):
        submissionForm = self.SubmissionForm(request.user, self.ass)
        return render(request, 'new.html', {'submissionForm': submissionForm, 'assignment': self.ass})


class SubmissionWithdrawView(LoginRequiredMixin, UpdateView):
    template_name = 'withdraw.html'
    model = Submission
    form_class = modelform_factory(Submission, fields=[])  # make form_valid() work
    success_url = reverse_lazy('dashboard')

    def get_object(self, queryset=None):
        submission = super().get_object(queryset)
        if not submission.can_withdraw(user=self.request.user):
            raise PermissionDenied(
                "Withdrawal for this assignment is no longer possible, or you are unauthorized to access that submission.")
        return submission

    def form_valid(self, form):
        messages.info(self.request, 'Submission successfully withdrawn.')
        self.object.state = Submission.WITHDRAWN
        self.object.save()
        return super().form_valid(form)


class SubmissionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'update.html'
    model = Submission
    form_class = SubmissionFileUpdateForm
    success_url = reverse_lazy('dashboard')

    def get_object(self, queryset=None):
        submission = super().get_object(queryset)
        if not submission.can_reupload():
            raise PermissionDenied("Update of submission not / no longer possible.")
        if self.request.user not in submission.authors.all():
            raise PermissionDenied("Update of submission is only allowed for authors.")
        return submission

    def form_valid(self, form):
        upload_file = self.request.FILES['attachment']
        new_file = SubmissionFile(
            attachment=form.files['attachment'],
            original_filename=upload_file.name)
        new_file.save()
        # fix status of old uploaded file
        self.object.file_upload.replaced_by = new_file
        self.object.file_upload.save()
        # store new file for submissions
        self.object.file_upload = new_file
        self.object.state = self.object.get_initial_state()
        self.object.notes = form.data['notes']
        self.object.save()
        messages.info(self.request, 'Submission files successfully updated.')
        return super().form_valid(form)


class AttachmentFileView(LoginRequiredMixin, BinaryDownloadMixin, DetailView):
    model = Submission

    def get_object(self, queryset=None):
        subm = super().get_object(queryset)
        if not (self.request.user in subm.authors.all() or self.request.user.is_staff):
            raise PermissionDenied()
        self.f = subm.file_upload.attachment
        self.fname = subm.file_upload.basename()
        return subm


class GradingFileView(LoginRequiredMixin, BinaryDownloadMixin, DetailView):
    model = Submission

    def get_object(self, queryset=None):
        subm = super().get_object(queryset)
        if not (self.request.user in subm.authors.all() or self.request.user.is_staff):
            raise PermissionDenied()
        self.f = subm.grading_file
        self.fname = os.path.basename(subm.grading_file.name)
        return subm


class DescriptionFileView(LoginRequiredMixin, BinaryDownloadMixin, DetailView):
    model = Assignment

    def get_object(self, queryset=None):
        ass = super().get_object(queryset)
        self.f = ass.description
        self.fname = self.f.name[self.f.name.rfind('/') + 1:]
        return ass

