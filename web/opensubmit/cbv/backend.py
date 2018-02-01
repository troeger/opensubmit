from django.views.generic import TemplateView, DetailView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


from opensubmit.models import Submission, Assignment
from opensubmit.models.userprofile import move_user_data


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class PreviewView(StaffRequiredMixin, DetailView):
    template_name = 'file_preview.html'
    model = Submission


class DuplicatesView(StaffRequiredMixin, DetailView):
    template_name = 'duplicates.html'
    model = Assignment


class MergeUsersView(StaffRequiredMixin, TemplateView):
    template_name = 'mergeusers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['primary'] = get_object_or_404(User, pk=kwargs['primary_pk'])
        context['secondary'] = get_object_or_404(User, pk=kwargs['secondary_pk'])
        return context

    def post(self, request, *args, **kwargs):
        primary = get_object_or_404(User, pk=kwargs['primary_pk'])
        secondary = get_object_or_404(User, pk=kwargs['secondary_pk'])
        try:
            move_user_data(primary, secondary)
            messages.info(request, 'Submissions moved to user %u.' %
                          (primary.pk))
        except Exception:
            messages.error(
                request, 'Error during data migration, nothing changed.')
            return redirect('admin:index')
        messages.info(request, 'User %u updated, user %u deleted.' % (primary.pk, secondary.pk))
        secondary.delete()
        return redirect('admin:index')
