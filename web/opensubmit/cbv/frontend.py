from django.views.generic import TemplateView, RedirectView
from django.views.generic.edit import UpdateView
from django.shortcuts import redirect
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory

from opensubmit.forms import SettingsForm
from opensubmit.models import UserProfile


class IndexView(TemplateView):
    template_name = 'index.html'

    def get(self, request):
        if request.user.is_authenticated():
            return redirect('dashboard')
        else:
            return super(IndexView, self).get(request)


@method_decorator(login_required, name='dispatch')
class LogoutView(RedirectView):
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
    '''
    TODO: Weitermachen.
    '''
    template_name = 'courses.html'
    form_class = modelform_factory(UserProfile, fields=['courses'])
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        messages.info(self.request, 'Your choice of courses was saved.')
        return super().form_valid(form)

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.request.user.profile.user_courses()
        return context
