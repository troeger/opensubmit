from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_managers, send_mail
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import smart_text
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import modelform_factory
from forms import SettingsForm, getSubmissionForm, SubmissionFileForm
from models import SubmissionFile, Submission, Assignment, TestMachine, Course, UserProfile, db_fixes
from openid2rp.django.auth import linkOpenID, preAuthenticate, AX, getOpenIDs
from settings import JOB_EXECUTOR_SECRET, MAIN_URL, LOGIN_DESCRIPTION, OPENID_PROVIDER
from models import inform_student, inform_course_owner
from datetime import timedelta, datetime
import urllib, os, tempfile, shutil, StringIO, zipfile, tarfile

def index(request):
    if request.user.is_authenticated():
        db_fixes(request.user)
        return redirect('dashboard')

    return render(request, 'index.html', {'login_description': LOGIN_DESCRIPTION})

def about(request):
    return render(request, 'about.html')

@login_required
def logout(request):
    auth.logout(request)
    return redirect('index')

@login_required
def settings(request):
    if request.POST:
        settingsForm=SettingsForm(request.POST, instance=request.user)
        if settingsForm.is_valid():
            settingsForm.save()
            messages.info(request, 'User settings saved.')
            return redirect('dashboard')
    else:
        settingsForm=SettingsForm(instance=request.user)
    return render(request, 'settings.html', {'settingsForm': settingsForm})

@login_required
def courses(request):
    UserProfileForm = modelform_factory(UserProfile, fields=['courses'])
    profile = UserProfile.objects.get(user=request.user)
    if request.POST:
        coursesForm=UserProfileForm(request.POST, instance=profile)
        if coursesForm.is_valid():
            coursesForm.save()
            messages.info(request, 'You choice was saved.')
            return redirect('dashboard')
    else:
        coursesForm=UserProfileForm(instance=profile)
    return render(request, 'courses.html', {'coursesForm': coursesForm})    

def download(request, obj_id, filetype, secret=None):
    if filetype=="attachment":
        subm = get_object_or_404(Submission, pk=obj_id)
        if not (request.user in subm.authors.all() or request.user.is_staff):
		return HttpResponseForbidden()
        f=subm.file_upload.attachment
        fname=subm.file_upload.basename()
    elif filetype=="validity_testscript":
        ass = get_object_or_404(Assignment, pk=obj_id)
        f=ass.attachment_test_validity
        fname=f.name[f.name.rfind('/')+1:]
    elif filetype=="full_testscript":
        ass = get_object_or_404(Assignment, pk=obj_id)
        f=ass.attachment_test_full
        fname=f.name[f.name.rfind('/')+1:]
    else:
        raise Http404        
    response=HttpResponse(f, content_type='application/binary')
    response['Content-Disposition'] = 'attachment; filename="%s"'%fname
    return response

@csrf_exempt
def jobs(request, secret):
    # This is the view used by the executor.py scripts for getting / putting the test results.
    #
    # Fetching some file for testing is changing the database, so using GET here is not really RESTish. Whatever.
    #
    # A visible shared secret in the request is no problem, since the executors come
    # from trusted networks. The secret only protects this view from outside foreigners.
    #import pdb; pdb.set_trace()
    if secret != JOB_EXECUTOR_SECRET:
        raise PermissionDenied
    if request.method == "GET":
        try:
            machine = TestMachine.objects.get(host=request.get_host())
            machine.last_contact=datetime.now()
            machine.save()
        except:
            # ask for configuration of new execution hosts by returning the according action
            machine = TestMachine( host=request.get_host(), last_contact=datetime.now() )
            machine.save()
            response=HttpResponse()
            response['Action'] = 'get_config'
            response['MachineId'] = machine.pk
            return response
        subm = Submission.pending_student_tests.all()
        if len(subm) == 0:
            subm = Submission.pending_full_tests.all()
            if len(subm) == 0:
                raise Http404
        for sub in subm:
            assert(sub.file_upload)     # must be given when the state model is correct
            # only deliver jobs that are unfetched so far, or where the executor should have finished meanwhile
            # it may happen in special cases that stucked executors deliver their result after the timeout
            # this is not really a problem, since the result remains the same for the same file
            #TODO: Make this a part of the original query
            #TODO: Count number of attempts to leave the same state, mark as finally failed in case; alternatively, the executor must always deliver a re.
            if (not sub.file_upload.fetched) or (sub.file_upload.fetched + timedelta(seconds=sub.assignment.attachment_test_timeout) < timezone.now()):
                if sub.file_upload.fetched:
                    # Stuff that has timed out
                    # we mark it as failed so that the user gets informed
                    #TODO:  Late delivery for such a submission by the executor witll break everything
		    sub.file_upload.fetched = None
                    if sub.state == Submission.TEST_COMPILE_PENDING:
                        sub.state = Submission.TEST_COMPILE_FAILED
                        sub.file_upload.test_compile = "Killed due to non-reaction on timeout signals. Please check your application for deadlocks or keyboard input."
                        inform_student(sub, sub.state)
                    if sub.state == Submission.TEST_VALIDITY_PENDING:
                        sub.file_upload.test_validity = "Killed due to non-reaction on timeout signals. Please check your application for deadlocks or keyboard input."
                        sub.state = Submission.TEST_VALIDITY_FAILED
                        inform_student(sub, sub.state)
                    if sub.state == Submission.TEST_FULL_PENDING:
                        sub.file_upload.test_full = "Killed due to non-reaction on timeout signals. Student not informed, since this was the full test."
                        sub.state = Submission.TEST_FULL_FAILED
                    sub.file_upload.save()
                    sub.save()
                    continue
                # create HTTP response with file download
                f=sub.file_upload.attachment
                # on dev server, we sometimes have stale database entries
                if not os.access(f.path, os.F_OK):
                    mail_managers('Warning: Missing file','Missing file on storage for submission file entry %u: %s'%(sub.file_upload.pk, str(sub.file_upload.attachment)), fail_silently=True)
                    continue
                response=HttpResponse(f, content_type='application/binary')
                response['Content-Disposition'] = 'attachment; filename="%s"'%sub.file_upload.basename()
                response['SubmissionFileId'] = str(sub.file_upload.pk)
                response['Timeout'] = sub.assignment.attachment_test_timeout
                if sub.state == Submission.TEST_COMPILE_PENDING:
                    response['Action'] = 'test_compile'
                elif sub.state == Submission.TEST_VALIDITY_PENDING:
                    response['Action'] = 'test_validity'
                    # reverse() is messing up here when we have to FORCE_SCRIPT case, so we do manual URL construction
                    response['PostRunValidation'] = MAIN_URL+"/download/%u/validity_testscript/secret=%s"%(sub.assignment.pk, JOB_EXECUTOR_SECRET)
                elif sub.state == Submission.TEST_FULL_PENDING or sub.state == Submission.CLOSED_TEST_FULL_PENDING:
                    response['Action'] = 'test_full'
                    # reverse() is messing up here when we have to FORCE_SCRIPT case, so we do manual URL construction
                    response['PostRunValidation'] = MAIN_URL+"/download/%u/full_testscript/secret=%s"%(sub.assignment.pk, JOB_EXECUTOR_SECRET)
                else:
                    assert(False)
                # store date of fetching for determining jobs stucked at the executor
                sub.file_upload.fetched=timezone.now()
                sub.file_upload.save()
		# 'touch' submission so that it becomes sorted to the end of the queue if something goes wrong
		sub.modified = timezone.now()
		sub.save()
                return response
        # no feasible match in the list of possible jobs
        raise Http404

    elif request.method == "POST":
        # first check if this is just configuration data, and not a job result
        if request.POST['Action'] == 'get_config':
            machine = TestMachine.objects.get(pk=int(request.POST['MachineId']))
            machine.config = request.POST['Config']
            machine.save()
            return HttpResponse(status=201)

        # executor.py is providing the results as POST parameters
        sid = request.POST['SubmissionFileId']
        submission_file=get_object_or_404(SubmissionFile, pk=sid)
        sub=submission_file.submissions.all()[0]
        error_code = int(request.POST['ErrorCode'])
        if request.POST['Action'] == 'test_compile' and sub.state == Submission.TEST_COMPILE_PENDING:
            submission_file.test_compile = request.POST['Message']
            if error_code == 0:
                if sub.assignment.attachment_test_validity:
                    sub.state = Submission.TEST_VALIDITY_PENDING
                elif sub.assignment.attachment_test_full:
                    sub.state = Submission.TEST_FULL_PENDING
                else:
                    sub.state = Submission.SUBMITTED_TESTED
                    inform_course_owner(request, sub)
            else:
                sub.state = Submission.TEST_COMPILE_FAILED                
            inform_student(sub, sub.state)
        elif request.POST['Action'] == 'test_validity' and sub.state == Submission.TEST_VALIDITY_PENDING:
            submission_file.test_validity = request.POST['Message']
            if error_code == 0:
                if sub.assignment.attachment_test_full:
                    sub.state = Submission.TEST_FULL_PENDING
                else:
                    sub.state = Submission.SUBMITTED_TESTED
                    inform_course_owner(request, sub)
            else:
                sub.state = Submission.TEST_VALIDITY_FAILED         
            inform_student(sub, sub.state)
        elif request.POST['Action'] == 'test_full' and sub.state == Submission.TEST_FULL_PENDING:
            submission_file.test_full = request.POST['Message']
            if error_code == 0:
                sub.state = Submission.SUBMITTED_TESTED
                inform_course_owner(request, sub)
            else:
                sub.state = Submission.TEST_FULL_FAILED                
            # full tests may be performed several times and are meant to be a silent activity
            # therefore, we send no mail to the student here
        elif request.POST['Action'] == 'test_full' and sub.state == Submission.CLOSED_TEST_FULL_PENDING:
            submission_file.test_full = request.POST['Message']
            sub.state = Submission.CLOSED
            # full tests may be performed several times and are meant to be a silent activity
            # therefore, we send no mail to the student here
        else:
            mail_managers('Warning: Inconsistent job state', str(sub.pk), fail_silently=True)
        submission_file.fetched=None            # makes the file fetchable again by executors, but now in a different state
        perf_data = request.POST['PerfData'].strip()
        if perf_data != "":
            submission_file.perf_data = perf_data
        else:
            submission_file.perf_data = None
        submission_file.save()
        sub.save()
        return HttpResponse(status=201)

@login_required
def dashboard(request):
    # if the user settings are not complete (e.f. adter OpenID registration), we MUST fix them first
    if not request.user.first_name or not request.user.last_name or not request.user.email:
        return redirect('settings')

    # render dashboard
    authored=request.user.authored.all().exclude(state=Submission.WITHDRAWN).order_by('-created')
    archived=request.user.authored.all().filter(state=Submission.WITHDRAWN).order_by('-created')
    username=request.user.get_full_name() + " <" + request.user.email + ">"
    waiting_for_action=[subm.assignment for subm in request.user.authored.all().exclude(state=Submission.WITHDRAWN)]
    user_courses = UserProfile.objects.get(user=request.user).courses.all()
    qs = Assignment.objects.filter(hard_deadline__gt = timezone.now())
    qs = qs.filter(publish_at__lt = timezone.now())
    qs = qs.filter(course__active__exact=True)
    qs = qs.filter(course__in=user_courses)
    qs = qs.order_by('soft_deadline').order_by('hard_deadline').order_by('title')
    openassignments = [ass for ass in qs if ass not in waiting_for_action]
    return render(request, 'dashboard.html', {
        'authored': authored,
        'archived': archived,
        'user': request.user,
        'username': username,
        'assignments': openassignments,
        'machines': TestMachine.objects.all()}
    )

@login_required
def details(request, subm_id):
    subm = get_object_or_404(Submission, pk=subm_id)
    if not (request.user in subm.authors.all() or request.user.is_staff):               # only authors should be able to look into submission details
	return HttpResponseForbidden()
    return render(request, 'details.html', {
        'submission': subm}
    )

@login_required
def new(request, ass_id):
    ass = get_object_or_404(Assignment, pk=ass_id)
    # get submission form according to the assignment type
    SubmissionForm=getSubmissionForm(ass)
    # Analyze submission data
    if request.POST:
        # we need to fill all forms here, so that they can be rendered on validation errors
        submissionForm=SubmissionForm(request.user, ass, request.POST, request.FILES)
        if submissionForm.is_valid(): 
            submission=submissionForm.save(commit=False)   # commit=False to set submitter in the instance
            submission.submitter=request.user
            submission.assignment=ass
            submission.state = submission.get_initial_state()
            # take uploaded file from extra field
            if ass.has_attachment:
                submissionFile=SubmissionFile(attachment=submissionForm.cleaned_data['attachment'])
                submissionFile.save()
                submission.file_upload=submissionFile                
            submission.save()
            submissionForm.save_m2m()               # because of commit=False, we first need to add the form-given authors
            submission.authors.add(request.user)    # submitter is always an author
            submission.save()
            messages.info(request, "New submission saved.")
            if submission.state == Submission.SUBMITTED:
                inform_course_owner(request, submission)
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct your submission information.")
    else:
        submissionForm=SubmissionForm(request.user, ass)
    return render(request, 'new.html', {'submissionForm': submissionForm, 
                                        'assignment': ass})

@login_required
def update(request, subm_id):
    # submission should only be editable by their creators
    submission = get_object_or_404(Submission, pk=subm_id)
    if request.user not in submission.authors.all():
        return redirect('dashboard')        
    if request.POST:
        fileForm=SubmissionFileForm(request.POST, request.FILES)
        if fileForm.is_valid():
            f=fileForm.save()
            # fix status of old uploaded file
            submission.file_upload.replaced_by=f
            submission.file_upload.save()
            # store new file for submissions
            submission.file_upload=f
            submission.state = submission.get_initial_state()
            submission.save()
            messages.info(request, 'Submission files successfully updated.')
            return redirect('dashboard')
    else:
        fileForm=SubmissionFileForm()
    return render(request, 'update.html', {'fileForm': fileForm,
                                           'submission': submission})

@login_required
@staff_member_required
def gradingtable(request, course_id):
    gradings={}
    course = get_object_or_404(Course, pk=course_id)
    assignments = course.assignments.all().order_by('title')
    # find all gradings per author and assignment
    for assignment in assignments:        
        for submission in assignment.submissions.all().filter(state=Submission.CLOSED):
            for author in submission.authors.all():
                if author not in gradings.keys():
                    gradings[author] = {assignment.pk : submission.grading}
                else:
                    gradings[author][assignment.pk] = submission.grading
    # prepare gradings per author + assignment for rendering
    resulttable=[]
    for author, gradlist in gradings.iteritems():
        columns=[]
        numpassed=0
        columns.append(author.last_name)
        columns.append(author.first_name)
        for assignment in assignments:
            if assignment.pk in gradlist:
                if gradlist[assignment.pk] != None:
			passed = gradlist[assignment.pk].means_passed
			columns.append(gradlist[assignment.pk])
			if passed:
			    numpassed += 1
                else:
                        columns.append('-')		
            else:
                columns.append('-')
        columns.append("%s / %s"%(numpassed, len(assignments)))
        resulttable.append(columns)
    return render(request, 'gradingtable.html', {'course': course, 'assignments': assignments,'resulttable': sorted(resulttable)})

@login_required
@staff_member_required
def coursearchive(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    coursename = course.title.replace(" ","_").lower()

    # we need to create the result ZIP file in memory to not leave garbage on the server
    output = StringIO.StringIO()
    z = zipfile.ZipFile(output, 'w') 

    # recurse through database and add according submitted files to in-memory archive
    coursedir = coursename
    assignments = course.assignments.order_by('title')
    for ass in assignments:
        assdir = coursedir+'/'+ass.title.replace(" ","_").lower()
        for sub in ass.submissions.all().order_by('submitter'):
            # unpack student data to temporary directory
            # os.chroot is not working with tarfile support
            tempdir=tempfile.mkdtemp()
            if zipfile.is_zipfile(sub.file_upload.absolute_path()):
                f=zipfile.ZipFile(sub.file_upload.absolute_path(), 'r')
                f.extractall(tempdir)
            elif tarfile.is_tarfile(sub.file_upload.absolute_path()):
                tar = tarfile.open(sub.file_upload.absolute_path())
                tar.extractall(tempdir)
                tar.close()
            else:
                # unpacking not possible, just copy it
                shutil.copyfile(sub.file_upload.absolute_path(), tempdir+"/"+sub.file_upload.basename())
            # Create final ZIP file
            state = sub.state_for_students().replace(" ","_").lower()
            submitter = "user"+str(sub.submitter.pk) 
            if sub.modified:
                modified = sub.modified.strftime("%Y_%m_%d_%H_%M_%S")
            else:
                modified = sub.created.strftime("%Y_%m_%d_%H_%M_%S")
            submdir = "%s/%s/%s_%s/"%(assdir, submitter, modified, state )
            for root, dirs, files in os.walk(tempdir):
                for f in files:
                    z.write(root+"/"+f, submdir+'student_files/'+f, zipfile.ZIP_DEFLATED)
            # add text file with additional information
            info = tempfile.NamedTemporaryFile()
            info.write("Status: %s\n\n"%sub.state_for_students())
            info.write("Submitter: %s\n\n"%submitter)
            info.write("Last modification: %s\n\n"%modified)
            info.write("Authors: ")
            for auth in sub.authors.all():
                author="user"+str(auth.pk)	
                info.write("%s,"%author)
            info.write("\n")
            if sub.grading:
                info.write("Grading: %s\n\n"%str(sub.grading))
            if sub.notes:
		notes=smart_text(sub.notes).encode('utf8')
                info.write("Author notes:\n-------------\n%s\n\n"%notes)
            if sub.grading_notes:
		notes=smart_text(sub.grading_notes).encode('utf8')
                info.write("Grading notes:\n--------------\n%s\n\n"%notes)
            info.flush()    # no closing here, because it disappears then
            z.write(info.name, submdir+"info.txt")
    z.close()
    # go back to start in ZIP file so that Django can deliver it
    output.seek(0)
    response = HttpResponse(output, mimetype = "application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s.zip'%coursename
    return response

@login_required
def machine(request, machine_id):
    machine = get_object_or_404(TestMachine, pk=machine_id)
    queue = Submission.pending_student_tests.all()
    additional = len(Submission.pending_full_tests.all())
    return render(request, 'machine.html', {'machine': machine, 'queue': queue, 'additional': additional})

@login_required
def withdraw(request, subm_id):
    # submission should only be deletable by their creators
    submission = get_object_or_404(Submission, pk=subm_id)
    if (request.user not in submission.authors.all()) or (not submission.can_withdraw()):
        return redirect('dashboard')        
    if "confirm" in request.POST:
        submission.state=Submission.WITHDRAWN
        submission.save()
        messages.info(request, 'Submission successfully withdrawn.')
        inform_course_owner(request, submission)
        return redirect('dashboard')
    else:
        return render(request, 'withdraw.html', {'submission': submission})

@require_http_methods(['GET', 'POST'])
def login(request):
    GET  = request.GET
    POST = request.POST

    if 'authmethod' in GET:
        # first stage of OpenID authentication
        if request.GET['authmethod']=="openid":
            return preAuthenticate(OPENID_PROVIDER, MAIN_URL+"/login?openidreturn")
        else:
            return redirect('index')

    elif 'openidreturn' in GET:
        user = auth.authenticate(openidrequest=request)

        if user.is_anonymous():    
            user_name = None
            email     = None

            user_sreg = user.openid_sreg
            user_ax   = user.openid_ax

            # not known to the backend so far, create it transparently
            if 'nickname' in user_sreg:
                user_name = unicode(user_sreg['nickname'],'utf-8')[:29]

            if 'email' in user_sreg:         
                email = unicode(user_sreg['email'],'utf-8')#[:29]

            if AX.email in user_ax:
                email = unicode(user_ax[AX.email],'utf-8')#[:29]

            # no username given, register user with his e-mail address as username
            if not user_name and email:
                new_user = User(username=email[:29], email=email)

            # both, username and e-mail were not given, use a timestamp as username
            elif not user_name and not email:
                now = timezone.now()
                user_name = 'Anonymous %u%u%u%u' % (now.hour, now.minute,\
                                                    now.second, now.microsecond)
                new_user = User(username=user_name)

            # username and e-mail were given; great - register as is
            elif user_name and email:
                new_user = User(username=user_name, email=email)

            # username given but no e-mail - at least we know how to call him
            elif user_name and not email:
                new_user = User(username=user_name)

            if AX.first in user_ax:
                new_user.first_name = unicode(user_ax[AX.first],'utf-8')[:29]

            if AX.last in user_ax:
                new_user.last_name=unicode(user_ax[AX.last],'utf-8')[:29]

            new_user.is_active = True
            new_user.save()

            linkOpenID(new_user, user.openid_claim)
            mail_managers('New user', str(new_user), fail_silently=True)
            messages.info(request, 'We created a new account for you. Please click again to enter the system.')
            return redirect('index')

        auth.login(request, user)
        return redirect('dashboard')
    else:
        return redirect('index')

@staff_member_required
def manual_submit(request, ass_id):
    ''' Manual submission of assignment solutions by the course administrator.'''

    from forms import getSubmissionForm
    assignment = get_object_or_404(Assignment, pk=ass_id)
    SubmissionForm = getSubmissionForm(assignment)
    submissionForm = SubmissionForm(request.user, assignment)
    return render(request, 'manual_submit.html', {'submissionForm': submissionForm, 
                                        'assignment': assignment})

