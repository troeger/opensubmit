import os

import json
import StringIO
import shutil
import tarfile
import tempfile
import urllib
import zipfile

from datetime import timedelta, datetime

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.mail import mail_managers, send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import smart_text
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import modelform_factory

from forms import SettingsForm, getSubmissionForm, SubmissionFileUpdateForm
from models import user_courses, SubmissionFile, Submission, Assignment, TestMachine, Course, UserProfile, db_fixes
from models import inform_student, inform_course_owner, open_assignments
from settings import JOB_EXECUTOR_SECRET, MAIN_URL


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
    return render(request, 'courses.html', {'coursesForm': coursesForm})


@login_required
def dashboard(request):
    db_fixes(request.user)

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
        'courses' : user_courses(request.user),
        'assignments': open_assignments(request.user),
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

    if not ass.is_visible(user=request.user):
        raise Http404()

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
                inform_course_owner(request, submission)
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
        columns.append(author.last_name)
        columns.append(author.first_name)
        for assignment in assignments:
            if assignment.pk in gradlist:
                if gradlist[assignment.pk] is not None:
                    passed = gradlist[assignment.pk].means_passed
                    columns.append(gradlist[assignment.pk])
                    if passed:
                        numpassed += 1
                else:
                    columns.append('-')
            else:
                columns.append('-')
        columns.append("%s / %s" % (numpassed, len(assignments)))
        resulttable.append(columns)
    return render(request, 'gradingtable.html', {'course': course, 'assignments': assignments, 'resulttable': sorted(resulttable)})


@login_required
@staff_member_required
def coursearchive(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    coursename = course.title.replace(" ", "_").lower()

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
                # unpack student data to temporary directory
                # os.chroot is not working with tarfile support
                tempdir = tempfile.mkdtemp()
                if zipfile.is_zipfile(sub.file_upload.absolute_path()):
                    f = zipfile.ZipFile(sub.file_upload.absolute_path(), 'r')
                    f.extractall(tempdir)
                elif tarfile.is_tarfile(sub.file_upload.absolute_path()):
                    tar = tarfile.open(sub.file_upload.absolute_path())
                    tar.extractall(tempdir)
                    tar.close()
                else:
                    # unpacking not possible, just copy it
                    shutil.copyfile(sub.file_upload.absolute_path(), tempdir + "/" + sub.file_upload.basename())
                # Create final ZIP file
                allfiles = [(subdir, files) for (subdir, dirs, files) in os.walk(tempdir)] 
                for subdir, files in allfiles:
                    for f in files:
                        zip_relative_dir = subdir.replace(tempdir, "")     
                        z.write(subdir + "/" + f, submdir + 'student_files/%s/%s'%(zip_relative_dir, f), zipfile.ZIP_DEFLATED)

            # add text file with additional information
            info = tempfile.NamedTemporaryFile()
            info.write("Status: %s\n\n" % sub.state_for_students())
            info.write("Submitter: %s\n\n" % submitter)
            info.write("Last modification: %s\n\n" % modified)
            info.write("Authors: ")
            for auth in sub.authors.all():
                author = "user" + str(auth.pk)
                info.write("%s," % author)
            info.write("\n")
            if sub.grading:
                info.write("Grading: %s\n\n" % str(sub.grading))
            if sub.notes:
                notes = smart_text(sub.notes).encode('utf8')
                info.write("Author notes:\n-------------\n%s\n\n" % notes)
            if sub.grading_notes:
                notes = smart_text(sub.grading_notes).encode('utf8')
                info.write("Grading notes:\n--------------\n%s\n\n" % notes)
            info.flush()    # no closing here, because it disappears then
            z.write(info.name, submdir + "info.txt")
    z.close()
    # go back to start in ZIP file so that Django can deliver it
    output.seek(0)
    response = HttpResponse(output, content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % coursename
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


@csrf_exempt
def machines(request, secret):
    ''' This is the view used by the executor.py scripts for putting machine details.
        A visible shared secret in the request is no problem, since the executors come
        from trusted networks. The secret only protects this view from outside foreigners.
    '''
    if secret != JOB_EXECUTOR_SECRET:
        raise PermissionDenied
    if request.method == "POST":
        try:
            # Find machine database entry for this host
            machine = TestMachine.objects.get(host=request.POST['Name'])
            machine.last_contact = datetime.now()
            machine.save()
        except:
            # Machine is not known so far, create new record
            machine = TestMachine(host=request.POST['Name'], last_contact=datetime.now())
            machine.save()
        # POST request contains all relevant machine information
        machine.config = request.POST['Config']
        machine.save()
        return HttpResponse(status=201)
    else:
        return HttpResponse(status=500)


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
        inform_course_owner(request, submission)
        return redirect('dashboard')
    else:
        return render(request, 'withdraw.html', {'submission': submission})


