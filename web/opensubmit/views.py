import os

import json
import StringIO
import shutil
import tarfile
import tempfile
import urllib
import zipfile
import csv

from datetime import timedelta, datetime

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.mail import mail_managers, send_mail, send_mass_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import modelform_factory
from blti import lti_provider

from forms import SettingsForm, getSubmissionForm, SubmissionFileUpdateForm, MailForm
from models import SubmissionFile, Submission, Assignment, TestMachine, Course, UserProfile
from models.userprofile import db_fixes, move_user_data
from models.course import lti_secret
from settings import JOB_EXECUTOR_SECRET, MAIN_URL
from social import passthrough


def index(request):
    if request.user.is_authenticated():
        return redirect('dashboard')

    return render(request, 'index.html', {})

@login_required
def logout(request):
    auth.logout(request)
    return redirect('index')

@login_required
def settings(request):
    if request.POST:
        settingsForm = SettingsForm(request.POST, instance=request.user)
        if settingsForm.is_valid():
            settingsForm.save()
            messages.info(request, 'User settings saved.')
            return redirect('dashboard')
    else:
        settingsForm = SettingsForm(instance=request.user)
    return render(request, 'settings.html', {'settingsForm': settingsForm})


@login_required
def courses(request):
    UserProfileForm = modelform_factory(UserProfile, fields=['courses'])
    profile = UserProfile.objects.get(user=request.user)
    if request.POST:
        coursesForm = UserProfileForm(request.POST, instance=profile)
        if coursesForm.is_valid():
            coursesForm.save()
            messages.info(request, 'You choice was saved.')
            return redirect('dashboard')
    else:
        coursesForm = UserProfileForm(instance=profile)
    return render(request, 'courses.html', {'coursesForm': coursesForm, 'courses': request.user.profile.user_courses()})


@login_required
def dashboard(request):
    # Fix database on lower levels for the current user
    db_fixes(request.user)
    profile = request.user.profile

    # If this is pass-through authentication, we can determine additional information
    if 'passthroughauth' in request.session:
        if 'ltikey' in request.session['passthroughauth']:
            # User coming through LTI. Check the course having this LTI key and enable it for the user.
            try:
                ltikey = request.session['passthroughauth']['ltikey']
                request.session['ui_disable_logout']=True
                course = Course.objects.get(lti_key=ltikey)
                profile.courses.add(course)
                profile.save()
            except:
                # This is only a comfort function, so we should not crash the app if that goes wrong
                pass

    # if the user settings are not complete (e.f. adter OpenID registration), we MUST fix them first
    if not request.user.first_name or not request.user.last_name or not request.user.email:
        return redirect('settings')

    # render dashboard
    authored = request.user.authored.all().exclude(state=Submission.WITHDRAWN).order_by('-created')
    archived = request.user.authored.all().filter(state=Submission.WITHDRAWN).order_by('-created')
    username = request.user.get_full_name() + " <" + request.user.email + ">"
    return render(request, 'dashboard.html', {
        'authored': authored,
        'archived': archived,
        'user': request.user,
        'username': username,
        'courses' : request.user.profile.user_courses(),
        'assignments': request.user.profile.open_assignments(),
        'machines': TestMachine.objects.all()}
    )


@login_required
def details(request, subm_id):
    subm = get_object_or_404(Submission, pk=subm_id)
    if not (request.user in subm.authors.all() or request.user.is_staff):               # only authors should be able to look into submission details
        raise PermissionDenied()
    return render(request, 'details.html', {
        'submission': subm}
    )


@login_required
def new(request, ass_id):
    ass = get_object_or_404(Assignment, pk=ass_id)

    # Check whether submissions are allowed.
    if not ass.can_create_submission(user=request.user):
        raise PermissionDenied("You are not allowed to create a submission for this assignment")

    # get submission form according to the assignment type
    SubmissionForm = getSubmissionForm(ass)

    # Analyze submission data
    if request.POST:
        if 'authors' in request.POST:
            authors = map(lambda s: User.objects.get(pk=int(s)), request.POST['authors'].split(','))
            if not ass.authors_valid(authors):
                raise PermissionDenied("The given list of co-authors is invalid!")

        # we need to fill all forms here, so that they can be rendered on validation errors
        submissionForm = SubmissionForm(request.user, ass, request.POST, request.FILES)
        if submissionForm.is_valid():
            submission = submissionForm.save(commit=False)   # commit=False to set submitter in the instance
            submission.submitter = request.user
            submission.assignment = ass
            submission.state = submission.get_initial_state()
            # take uploaded file from extra field
            if ass.has_attachment:
                submissionFile = SubmissionFile(attachment=submissionForm.cleaned_data['attachment'])
                submissionFile.save()
                submission.file_upload = submissionFile
            submission.save()
            submissionForm.save_m2m()               # because of commit=False, we first need to add the form-given authors
            submission.save()
            messages.info(request, "New submission saved.")
            if submission.state == Submission.SUBMITTED:
                submission.inform_course_owner(request)
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct your submission information.")
    else:
        submissionForm = SubmissionForm(request.user, ass)
    return render(request, 'new.html', {'submissionForm': submissionForm,
                                        'assignment': ass})


@login_required
def update(request, subm_id):
    # Submission should only be editable by their creators
    submission = get_object_or_404(Submission, pk=subm_id)
    # Somebody may bypass the template check by sending direct POST form data
    if not submission.can_reupload():
        raise SuspiciousOperation("Update of submission %s is not allowed at this time." % str(subm_id))
    if request.user not in submission.authors.all():
        return redirect('dashboard')
    if request.POST:
        updateForm = SubmissionFileUpdateForm(request.POST, request.FILES)
        if updateForm.is_valid():
            new_file = SubmissionFile(attachment=updateForm.files['attachment'])
            new_file.save()
            # fix status of old uploaded file
            submission.file_upload.replaced_by = new_file
            submission.file_upload.save()
            # store new file for submissions
            submission.file_upload = new_file
            submission.state = submission.get_initial_state()
            submission.notes = updateForm.data['notes']
            submission.save()
            messages.info(request, 'Submission files successfully updated.')
            return redirect('dashboard')
    else:
        updateForm = SubmissionFileUpdateForm(instance=submission)
    return render(request, 'update.html', {'submissionFileUpdateForm': updateForm,
                                           'submission': submission})

@login_required
@staff_member_required
def mergeusers(request):
    '''
        Offers an intermediate admin view to merge existing users.
    '''
    if request.method == 'POST':
        primary=get_object_or_404(User, pk=request.POST['primary_id'])
        secondary=get_object_or_404(User, pk=request.POST['secondary_id'])
        try:
            move_user_data(primary, secondary)
            messages.info(request, 'Submissions moved to user %u.'%(primary.pk))
        except:
            messages.error(request, 'Error during data migration, nothing changed.')
            return redirect('admin:index')
        messages.info(request, 'User %u deleted.'%(secondary.pk))
        secondary.delete()
        return redirect('admin:index')
    primary=get_object_or_404(User, pk=request.GET['primary_id'])
    secondary=get_object_or_404(User, pk=request.GET['secondary_id'])
    # Determine data to be migrated
    return render(request, 'mergeusers.html', {'primary': primary, 'secondary': secondary})

@login_required
@staff_member_required
def preview(request, subm_id):
    '''
        Renders a preview of the uploaded student archive.
        This is only intended for the grading procedure, so staff status is needed.
    '''
    submission = get_object_or_404(Submission, pk=subm_id)
    if submission.file_upload.is_archive():
        return render(request, 'file_preview.html', {'submission': submission, 'previews': submission.file_upload.archive_previews()})
    else:
        return redirect(submission.file_upload.get_absolute_url())

@login_required
@staff_member_required
def perftable(request, ass_id):
    assignment = get_object_or_404(Assignment, pk=ass_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="perf_assignment%u.csv"'%assignment.pk
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Assignment','Submission ID','Authors','Performance Data'])
    for sub in assignment.submissions.all():
        result = sub.get_fulltest_result()
        if result:
            writer.writerow([sub.assignment, sub.pk, ", ".join(sub.authors.values_list('username', flat=True).order_by('username')), result.perf_data])
    return response

@login_required
@staff_member_required
def duplicates(request, ass_id):
    assignment = get_object_or_404(Assignment, pk=ass_id)
    return render(request, 'duplicates.html', {
        'assignment': assignment
    })

@login_required
@staff_member_required
def gradingtable(request, course_id):
    gradings = {}
    course = get_object_or_404(Course, pk=course_id)
    assignments = course.assignments.all().order_by('title')
    # find all gradings per author and assignment
    for assignment in assignments:
        for submission in assignment.submissions.all().filter(state=Submission.CLOSED):
            for author in submission.authors.all():
                if author not in gradings.keys():
                    gradings[author] = {assignment.pk: submission.grading}
                else:
                    gradings[author][assignment.pk] = submission.grading
    # prepare gradings per author + assignment for rendering
    resulttable = []
    for author, gradlist in gradings.iteritems():
        columns = []
        numpassed = 0
        pointsum = 0
        columns.append(author.last_name)
        columns.append(author.first_name)
        if author.profile.student_id:
            columns.append(author.profile.student_id)
        else:
            columns.append('')
        for assignment in assignments:
            if assignment.pk in gradlist:
                grade = gradlist[assignment.pk]
                if grade is not None:
                    passed = grade.means_passed
                    columns.append(grade)
                    if passed:
                        numpassed += 1
                    try:
                        pointsum += int(str(grade))
                    except:
                        pass
                else:
                    columns.append('N/A')
            else:
                columns.append('')
        columns.append("%s / %s" % (numpassed, len(assignments)))
        columns.append("%u" % pointsum)
        resulttable.append(columns)
    return render(request, 'gradingtable.html', {'course': course, 'assignments': assignments, 'resulttable': sorted(resulttable)})

def _replace_placeholders(text, user, course):
    return text.replace("#FIRSTNAME#", user.first_name.strip()) \
               .replace("#LASTNAME#", user.last_name.strip())   \
               .replace("#COURSENAME#", course.title.strip())

@login_required
@staff_member_required
def mail2all(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    # Re-compute list of recipients on every request, for latest updates
    students = User.objects.filter(profile__courses__pk = course_id)
    maillist = ','.join(students.values_list('email', flat=True))

    if request.method == "POST":
        if 'subject' in request.POST and 'message' in request.POST:
            # Initial form submission, render preview
            request.session['subject'] = request.POST['subject']
            request.session['message'] = request.POST['message']
            student = students[0]
            preview_subject = _replace_placeholders(request.POST['subject'], student, course)
            preview_message = _replace_placeholders(request.POST['message'], student, course)
            return render(request, 'mail_preview.html',
                            {'preview_subject': preview_subject,
                             'preview_message': preview_message,
                             'preview_from': request.user.email,
                             'course': course})
        elif 'subject' in request.session and 'message' in request.session:
            # Positive preview, send it
            data = [(_replace_placeholders(request.session['subject'], s, course),
                     _replace_placeholders(request.session['message'], s, course),
                     request.user.email,
                     [s.email]) for s in students]
            sent = send_mass_mail(data, fail_silently=True)
            messages.add_message(request, messages.INFO, '%u message(s) sent.'%sent)
            return redirect('teacher:index')

    # show empty form in all other cases
    mailform = MailForm()
    return render(request, 'mail_form.html', {'maillist': maillist, 'course': course, 'mailform': mailform })

@login_required
@staff_member_required
def coursearchive(request, course_id):
    '''
        Provides all course submissions and their information as archive download.
        For archiving purposes, since withdrawn submissions are included.
    '''
    course = get_object_or_404(Course, pk=course_id)
    coursename = course.directory_name()

    # we need to create the result ZIP file in memory to not leave garbage on the server
    output = StringIO.StringIO()
    z = zipfile.ZipFile(output, 'w')

    # recurse through database and add according submitted files to in-memory archive
    coursedir = coursename
    assignments = course.assignments.order_by('title')
    for ass in assignments:
        assdir = coursedir + '/' + ass.title.replace(" ", "_").lower()
        for sub in ass.submissions.all().order_by('submitter'):
            submitter = "user" + str(sub.submitter.pk)
            if sub.modified:
                modified = sub.modified.strftime("%Y_%m_%d_%H_%M_%S")
            else:
                modified = sub.created.strftime("%Y_%m_%d_%H_%M_%S")
            state = sub.state_for_students().replace(" ", "_").lower()
            submdir = "%s/%s/%s_%s/" % (assdir, submitter, modified, state)
            if sub.file_upload:
                # Copy student upload
                tempdir = tempfile.mkdtemp()
                sub.copy_file_upload(tempdir)
                # Add content to final ZIP file
                allfiles = [(subdir, files) for (subdir, dirs, files) in os.walk(tempdir)]
                for subdir, files in allfiles:
                    for f in files:
                        zip_relative_dir = subdir.replace(tempdir, "")
                        zip_relative_file = '%s/%s'%(zip_relative_dir.decode('utf-8', 'replace'), f.decode('utf-8', 'replace'))
                        z.write(subdir + "/" + f, submdir + 'student_files/%s'%zip_relative_file, zipfile.ZIP_DEFLATED)
            # add text file with additional information
            info = sub.info_file()
            z.write(info.name, submdir + "info.txt")
    z.close()

    # go back to start in ZIP file so that Django can deliver it
    output.seek(0)
    response = HttpResponse(output, content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % coursename
    return response

@login_required
@staff_member_required
def assarchive(request, ass_id):
    '''
        Provides all non-withdrawn submissions for an assignment as download.
        Intented for supporting offline correction.
    '''
    ass = get_object_or_404(Assignment, pk=ass_id)
    ass_name = ass.directory_name()

    # we need to create the result ZIP file in memory to not leave garbage on the server
    output = StringIO.StringIO()
    z = zipfile.ZipFile(output, 'w')

    # recurse through database and add according submitted files to in-memory archive
    for sub in Submission.valid_ones.filter(assignment=ass):
        submdir = "%s/%u/" % (ass_name, sub.pk)
        if sub.file_upload:
            # Copy student upload
            tempdir = tempfile.mkdtemp()
            sub.copy_file_upload(tempdir)
            # Add content to final ZIP file
            allfiles = [(subdir, files) for (subdir, dirs, files) in os.walk(tempdir)]
            for subdir, files in allfiles:
                for f in files:
                    zip_relative_dir = subdir.replace(tempdir, "")
                    zip_relative_file = '%s/%s'%(zip_relative_dir.decode('utf-8', 'replace'), f.decode('utf-8', 'replace'))
                    z.write(subdir + "/" + f, submdir + 'student_files/%s'%zip_relative_file, zipfile.ZIP_DEFLATED)

        # add text file with additional information
        info = sub.info_file()
        z.write(info.name, submdir + "info.txt")
    z.close()
    # go back to start in ZIP file so that Django can deliver it
    output.seek(0)
    response = HttpResponse(output, content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % ass_name
    return response


@login_required
def machine(request, machine_id):
    machine = get_object_or_404(TestMachine, pk=machine_id)
    try:
        config = filter(lambda x: x[1] != "", json.loads(machine.config))
    except:
        config = ""
    queue = Submission.pending_student_tests.all()
    additional = len(Submission.pending_full_tests.all())
    return render(request, 'machine.html', {'machine': machine, 'queue': queue, 'additional': additional, 'config': config})

@login_required
def withdraw(request, subm_id):
    # submission should only be deletable by their creators
    submission = get_object_or_404(Submission, pk=subm_id)
    if not submission.can_withdraw(user=request.user):
        raise PermissionDenied("Withdrawal for this assignment is no longer possible, or you are unauthorized to access that submission.")
    if "confirm" in request.POST:
        submission.state = Submission.WITHDRAWN
        submission.save()
        messages.info(request, 'Submission successfully withdrawn.')
        submission.inform_course_owner(request)
        return redirect('dashboard')
    else:
        return render(request, 'withdraw.html', {'submission': submission})

@lti_provider(consumer_lookup=lti_secret, site_url=MAIN_URL)
@require_POST
def lti(request, post_params, consumer_key, *args, **kwargs):
    '''
        Entry point for LTI consumers.

        This view is protected by the BLTI package decorator, which performs all the relevant OAuth signature checking. It also makes
        sure that the LTI consumer key and secret were ok. The latter ones are supposed to be configured in the admin interface.

        We can now trust on the provided data to be from the LTI provider.

        If everything worked out, we store the information the session for the Python Social passthrough provider, which is performing
        user creation and database storage.
    '''
    data={}
    data['ltikey']=post_params.get('oauth_consumer_key')
    # None of them is mandatory
    data['id']=post_params.get('user_id', None)
    data['username']=post_params.get('custom_username', None)
    data['last_name']=post_params.get('lis_person_name_family', None)
    data['email']=post_params.get('lis_person_contact_email_primary', None)
    data['first_name']=post_params.get('lis_person_name_given', None)
    request.session[passthrough.SESSION_VAR]=data
    return redirect(reverse('social:begin',args=['lti']))

