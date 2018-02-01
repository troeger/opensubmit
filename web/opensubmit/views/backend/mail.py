'''
OpenSubmit backend views that deal with mail sending.
'''

from django.views.generic import FormView, TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from opensubmit.views.helpers import StaffRequiredMixin
from opensubmit.forms import MailForm
from opensubmit.models import Course

RECV_LIST_SESSION_VAR = 'mail_receivers'


class MailFormView(FormView):
    '''
    Base class for a mail form.
    '''
    template_name = 'mail_form.html'
    form_class = MailForm

    # To be defined by derived class
    receivers = None
    no_receivers_msg = 'The list of receivers is empty.'
    no_receivers_redirect = 'index'

    def get_context_data(self, **kwargs):
        # Fetch general context first
        context = super().get_context_data(**kwargs)
        # Generate text list of receiver infos,
        # based on additional self.receivers info given
        # by derived class
        mailadrs_qs = self.receivers.order_by('email').distinct().values('first_name', 'last_name', 'email')
        mailadrs = [mailadr for mailadr in mailadrs_qs]
        # Store for later forms
        self.request.session[RECV_LIST_SESSION_VAR] = mailadrs
        # Store for this form
        context['receivers'] = mailadrs
        return context

    def render_to_response(self, context, **response_kwargs):
        if len(context['receivers']) == 0:
            messages.warning(self.request, self.no_receivers_msg)
            return redirect(self.no_receivers_redirect)
        else:
            return super().render_to_response(context, **response_kwargs)


class MailCourseView(StaffRequiredMixin, MailFormView):
    no_receivers_msg = 'No students in this course.'
    no_receivers_redirect = 'teacher:index'

    def get_context_data(self, **kwargs):
        # Prepare additional information for context generation
        course = get_object_or_404(Course, pk=self.kwargs['pk'])
        self.receivers = User.objects.filter(profile__courses__pk=course.pk)
        # Generate context
        return super().get_context_data(**kwargs)


class MailStudentsView(StaffRequiredMixin, MailFormView):
    no_receivers_msg = 'No mail receivers chosen.'
    no_receivers_redirect = 'teacher:index'

    def get_context_data(self, **kwargs):
        # Prepare additional information for context generation
        id_list = [int(val) for val in self.kwargs['pk_list'].split(',')]
        self.receivers = User.objects.filter(pk__in=id_list).distinct()
        # Generate context
        return super().get_context_data(**kwargs)


class MailPreviewView(StaffRequiredMixin, TemplateView):
    template_name = 'mail_preview.html'

    def _replace_placeholders(text, user):
        return text.replace("#FIRSTNAME#", user['first_name'].strip()) \
                   .replace("#LASTNAME#", user['last_name'].strip())

    def get_context_data(self, **kwargs):
        # Fetch general context first
        context = super().get_context_data(**kwargs)
        assert(RECV_LIST_SESSION_VAR in self.request.session)
        assert('subject' in self.request.POST)
        assert('message' in self.request.POST)
        data = [{'subject': self._replace_placeholders(self.request.POST['subject'], receiver),
                 'message': self._replace_placeholders(self.request.POST['message'], receiver),
                 'to': receiver['email']
                 } for receiver in self.request.session[RECV_LIST_SESSION_VAR]]
        # Store for later forms
        self.request.session['mail_data'] = data
        del self.request.session[RECV_LIST_SESSION_VAR]
        # Store for this form
        context['data'] = data
        return context

