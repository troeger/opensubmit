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
def gradingtable(request, course_id):
    author_submissions = {}
    course = get_object_or_404(Course, pk=course_id)
    assignments = course.assignments.all().order_by('title')
    # find all gradings per author and assignment
    for assignment in assignments:
        for submission in assignment.submissions.all().filter(state=Submission.CLOSED):
            for author in submission.authors.all():
                # author_submissions is a dict mapping authors to another dict
                # This second dict maps assignments to submissions (for this author)
                # A tuple as dict key does not help here, since we want to iterate over the assignments later
                if author not in list(author_submissions.keys()):
                    author_submissions[author] = {assignment.pk: submission}
                else:
                    author_submissions[author][assignment.pk] = submission
    resulttable = []
    for author, ass2sub in list(author_submissions.items()):
        columns = []
        numpassed = 0
        numgraded = 0
        pointsum = 0
        columns.append(author.last_name if author.last_name else '')
        columns.append(author.first_name if author.first_name else '')
        columns.append(
            author.profile.student_id if author.profile.student_id else '')
        columns.append(
            author.profile.study_program if author.profile.study_program else '')
        # Process all assignments in the table order, once per author (loop above)
        for assignment in assignments:
            if assignment.pk in ass2sub:
                # Ok, we have a submission for this author in this assignment
                submission = ass2sub[assignment.pk]
                if assignment.is_graded():
                    # is graded, make part of statistics
                    numgraded += 1
                    if submission.grading_means_passed():
                        numpassed += 1
                        try:
                            pointsum += int(str(submission.grading))
                        except Exception:
                            pass
                # considers both graded and ungraded assignments
                columns.append(submission.grading_value_text())
            else:
                # No submission for this author in this assignment
                # This may or may not be bad, so we keep it neutral here
                columns.append('-')
        columns.append("%s / %s" % (numpassed, numgraded))
        columns.append("%u" % pointsum)
        resulttable.append(columns)
    return render(request, 'gradingtable.html',
                  {'course': course, 'assignments': assignments,
                   'resulttable': sorted(resulttable)})


def _mail_form(request, users_qs):
    receivers_qs = users_qs.order_by('email').distinct().values('first_name', 'last_name', 'email')
    receivers = [receiver for receiver in receivers_qs]
    request.session['mail_receivers'] = receivers
    return render(request, 'mail_form.html', {'receivers': receivers, 'mailform': MailForm()})


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


@login_required
@staff_member_required
def coursearchive(request, course_id):
    '''
        Provides all course submissions and their information as archive download.
        For archiving purposes, since withdrawn submissions are included.
    '''
    output = io.BytesIO()
    z = zipfile.ZipFile(output, 'w')

    course = get_object_or_404(Course, pk=course_id)
    assignments = course.assignments.order_by('title')
    for ass in assignments:
        ass.add_to_zipfile(z)
        subs = ass.submissions.all().order_by('submitter')
        for sub in subs:
            sub.add_to_zipfile(z)

    z.close()
    # go back to start in ZIP file so that Django can deliver it
    output.seek(0)
    response = HttpResponse(
        output, content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % course.directory_name()
    return response


@login_required
@staff_member_required
def assarchive(request, ass_id):
    '''
        Provides all non-withdrawn submissions for an assignment as download.
        Intented for supporting offline correction.
    '''
    output = io.BytesIO()
    z = zipfile.ZipFile(output, 'w')

    ass = get_object_or_404(Assignment, pk=ass_id)
    ass.add_to_zipfile(z)
    subs = Submission.valid_ones.filter(assignment=ass).order_by('submitter')
    for sub in subs:
        sub.add_to_zipfile(z)

    z.close()
    # go back to start in ZIP file so that Django can deliver it
    output.seek(0)
    response = HttpResponse(
        output, content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % ass.directory_name()
    return response



