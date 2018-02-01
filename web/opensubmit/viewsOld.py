import json
import io
import zipfile
import csv

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mass_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import model_to_dict

from .forms import SettingsForm, getSubmissionForm, SubmissionFileUpdateForm, MailForm
from .models import SubmissionFile, Submission, Assignment, TestMachine, Course, UserProfile
from .models.userprofile import db_fixes, move_user_data
from .settings import MAIN_URL

import logging
logger = logging.getLogger('OpenSubmit')






@login_required
@staff_member_required
def mail_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    users = User.objects.filter(profile__courses__pk=course.pk)
    if users.count() == 0:
        messages.warning(request, 'No students in this course.')
        return redirect('teacher:index')
    else:
        return _mail_form(request, users)


@login_required
@staff_member_required
def mail_students(request, student_ids):
    id_list = [int(val) for val in student_ids.split(',')]
    users = User.objects.filter(pk__in=id_list).distinct()
    return _mail_form(request, users)


@login_required
@staff_member_required
def mail_preview(request):
    def _replace_placeholders(text, user):
        return text.replace("#FIRSTNAME#", user['first_name'].strip()) \
                   .replace("#LASTNAME#", user['last_name'].strip())

    if 'mail_receivers' in request.session and \
       'subject' in request.POST and \
       'message' in request.POST:
        data = [{'subject': _replace_placeholders(request.POST['subject'], receiver),
                 'message': _replace_placeholders(request.POST['message'], receiver),
                 'to': receiver['email']
                 } for receiver in request.session['mail_receivers']]

        request.session['mail_data'] = data
        del request.session['mail_receivers']
        return render(request, 'mail_preview.html', {'data': data})
    else:
        messages.error(request, 'Error while rendering mail preview.')
        return redirect('teacher:index')


@login_required
@staff_member_required
def mail_send(request):
    if 'mail_data' in request.session:
        tosend = [[d['subject'],
                   d['message'],
                   request.user.email,
                   [d['to']]]
                  for d in request.session['mail_data']]
        sent = send_mass_mail(tosend, fail_silently=True)
        messages.add_message(request, messages.INFO,
                             '%u message(s) sent.' % sent)
        del request.session['mail_data']
    else:
        messages.error(request, 'Error while preparing mail sending.')
    return redirect('teacher:index')




