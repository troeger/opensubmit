from datetime import datetime

from django.views.generic import TemplateView, RedirectView, ListView
from django.views.generic.edit import UpdateView
from django.shortcuts import redirect
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory, model_to_dict

from opensubmit.forms import SettingsForm
from opensubmit.models import UserProfile, Submission, TestMachine, Course
from opensubmit.models.userprofile import db_fixes


class IndexView(TemplateView):
    template_name = 'index.html'

    def get(self, request):
        if request.user.is_authenticated():
            return redirect('dashboard')
        else:
            return super(IndexView, self).get(request)


@method_decorator(login_required, name='dispatch')
class LogoutView(RedirectView):
    '''
    TODO: Not needed with Django 1.11, which has own LogoutView.
    '''
    permanent = False
    pattern_name = 'index'

    def get(self, request):
        auth.logout(request)
        return super().get(request)


@method_decorator(login_required, name='dispatch')
class SettingsView(UpdateView):
    template_name = 'settings.html'
    form_class = SettingsForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        messages.info(self.request, 'User settings saved.')
        return super().form_valid(form)

    def get_object(self, queryset=None):
        return self.request.user


@method_decorator(login_required, name='dispatch')
class CoursesView(UpdateView):
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


@method_decorator(login_required, name='dispatch')
class ArchiveView(ListView):
    template_name = 'archive.html'

    def get_queryset(self):
        archived = self.request.user.authored.all().exclude(assignment__course__active=False).filter(state=Submission.WITHDRAWN).order_by('-created')
        return archived


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
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
            messages.error(request, "Your user settings are incomplete.")

        return super().get(request)
