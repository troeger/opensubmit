from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_managers, send_mail
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from forms import SettingsForm, SubmissionWithGroupsForm, SubmissionWithoutGroupsForm, getSubmissionFilesFormset
from models import SubmissionFile, Submission, Assignment
from openid2rp.django.auth import linkOpenID, preAuthenticate, AX, getOpenIDs
from settings import JOB_EXECUTOR_SECRET, MAIN_URL
from models import inform_student, inform_course_owner
import urllib

def index(request):
    if request.user.is_authenticated():
        return redirect('dashboard')

    return render(request, 'index.html')

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

def testscript(request, ass_id, secret):
    #import pdb; pdb.set_trace()
    # This is the view used by the executor.py scripts for getting the test script for an assignment
    ass = get_object_or_404(Assignment, pk=ass_id)
    try:
        fname=ass.test_script.name[ass.test_script.name.rfind('/')+1:]
        response=HttpResponse(ass.test_script, content_type='application/binary')
        response['Content-Disposition'] = 'attachment; filename="%s"'%fname
        return response
    except:
        raise Http404

@csrf_exempt
def jobs(request, secret):
    #import pdb; pdb.set_trace()
    # This is the view used by the executor.py scripts for getting / putting the test results.
    #
    # Fetching some file for testing is changing the database, so using GET here is not really RESTish. Anyway.
    #
    # A visible shared secret in the request is no problem, since the executors come
    # from trusted networks. The secret only protects this view from outside foreigners.
    if secret != JOB_EXECUTOR_SECRET:
        raise PermissionDenied
    if request.method == "GET":
        # Hand over a pending job to be tested 
        # Compilation jobs have precedence, th oldest one wins
        subm = Submission.objects.filter(state=Submission.SUBMITTED_UNTESTED).order_by('created')
        if len(subm) == 0:
            subm = Submission.objects.filter(state=Submission.SUBMITTED_COMPILED).order_by('created')
            if len(subm) == 0:
                raise Http404
        for sub in subm:
            files=sub.active_files()
            if files:
                # create HTTP response with file download
                frecord=files[0]
                f=frecord.attachment
                fname=f.name[f.name.rfind('/')+1:]
                response=HttpResponse(f, content_type='application/binary')
                response['Content-Disposition'] = 'attachment; filename="%s"'%fname
                response['SubmissionFileId'] = str(frecord.pk)
                response['Timeout'] = sub.assignment.test_timeout
                if sub.state == Submission.SUBMITTED_UNTESTED:
                    response['Action'] = 'compile'
                elif sub.state == Submission.SUBMITTED_COMPILED:
                    response['Action'] = 'run'
                else:
                    assert(False)
                # If the assignment has a validation script, point the executor to the download
                if sub.assignment.test_script:
                    response['PostRunValidation'] = MAIN_URL+"/testscript/%u/secret=%s"%(sub.assignment.pk, JOB_EXECUTOR_SECRET)
                # store date of fetching for debugging purposes
                frecord.fetched=timezone.now()
                frecord.save()
                return response
        # No files found in the submissions
        raise Http404

    elif request.method == "POST":
        # executor.py is providing the results as POST parameters, so changing the names 
        # must be reflected here and there
        sid = request.POST['SubmissionFileId']
        submission_file=get_object_or_404(SubmissionFile, pk=sid)
        submission_file.error_code = request.POST['ErrorCode']
        submission_file.output = request.POST['Message']
        submission_file.save()
        subm=submission_file.submission
        if request.POST['Action'] == 'compile':
            if int(submission_file.error_code) == 0:
                subm.state = Submission.SUBMITTED_COMPILED
            else:
                subm.state = Submission.FAILED_COMPILE                
        elif request.POST['Action'] == 'run':
            if int(submission_file.error_code) == 0:
                subm.state = Submission.SUBMITTED_TESTED
                inform_course_owner(request, subm)
            else:
                subm.state = Submission.FAILED_EXEC
        else:
            assert(False)
        subm.save()
        inform_student(subm)
        return HttpResponse(status=201)

@login_required
def dashboard(request):
    authored=request.user.authored.order_by('-created')
    username=request.user.get_full_name() + " <" + request.user.email + ">"
    waiting_for_action=[subm.assignment for subm in request.user.authored.all().exclude(state=Submission.WITHDRAWN)]
    openassignments=[ass for ass in Assignment.open_ones.all().order_by('soft_deadline').order_by('hard_deadline') if ass not in waiting_for_action]
    return render(request, 'dashboard.html', {
        'authored': authored,
        'user': request.user,
        'username': username,
        'assignments': openassignments}
    )

@login_required
def new(request, ass_id):
    ass = get_object_or_404(Assignment, pk=ass_id)
    # Prepare the model form classes
    # Assignments with only one author need no author choice
    if ass.course.max_authors > 1:
        SubmissionForm=SubmissionWithGroupsForm
    else:
        SubmissionForm=SubmissionWithoutGroupsForm
    SubmissionFileFormSet = getSubmissionFilesFormset(ass)
    # Analyze submission data
    if request.POST:
        # we need to fill all forms here, so that they can be rendered on validation errors
        submissionForm=SubmissionForm(request.POST, request.FILES)
        submissionForm.removeUnwantedAuthors(request.user, ass)
        if ass.has_attachment:
            filesForm=SubmissionFileFormSet(request.POST, request.FILES)
        else:
            filesForm=None
        all_valid=False
        if submissionForm.is_valid(): 
        # ok, submission data is valid, but if the view has offered files, they must be valid too to start saving of all data
        # Therefore, we first determine overal validity and then start saving
            if ass.has_attachment:
                if filesForm.is_valid():
                    all_valid=True
            else:
                all_valid=True
        if all_valid:
            # whether files or not, it is valid now to save
            submission=submissionForm.save(commit=False)   # commit=False to set submitter in the instance
            submission.submitter=request.user
            submission.assignment=ass
            if submission.assignment.test_attachment:
                submission.state=Submission.SUBMITTED_UNTESTED
            else:
                submission.state=Submission.SUBMITTED
                inform_course_owner(request, submission)
            submission.save()
            submissionForm.save_m2m()               # because of commit=False, we first need to add the form-given authors
            submission.authors.add(request.user)    # submitter is always an author
            submission.save()
            # we can do this only after submission saving. At least we know here that it is valid
            if ass.has_attachment:
                files=filesForm.save(commit=False)
                for f in files:
                    f.submission=submission
                    f.save()
            # all saved
            messages.info(request, "New submission saved.")
            return redirect('dashboard')
    else:
        submissionForm=SubmissionForm()
        submissionForm.removeUnwantedAuthors(request.user, ass)
        filesForm=SubmissionFileFormSet(queryset=SubmissionFile.objects.none())
    return render(request, 'new.html', {'submissionForm': submissionForm, 
                                        'filesForm': filesForm,
                                        'assignment': ass})

@login_required
def update(request, subm_id):
    # submission should only be editable by their creators
    submission = get_object_or_404(Submission, pk=subm_id)
    if request.user not in submission.authors.all():
        return redirect('dashboard')        
    SubmissionFileFormSet = getSubmissionFilesFormset(submission.assignment)
    if request.POST:
        filesForm=SubmissionFileFormSet(request.POST, request.FILES)
        if filesForm.is_valid():
            # determine old files
            # TODO: This needs to properly hable the multiple file case
            # currently, we hack it by just replacing the first with the first
            oldfiles=list(submission.files.all())       # enforce QS evaluation by list()
            # now save new files
            files=filesForm.save(commit=False)
            for f in files:
                f.submission=submission
                f.replaced_by=None
                f.save()
                for oldfile in oldfiles:
                    oldfile.replaced_by=f
                    oldfile.save()
            # ok, all files save, now adjust the submission status
            submission.state = Submission.SUBMITTED_UNTESTED
            submission.save()
            messages.info(request, 'Submission files successfully updated.')
            return redirect('dashboard')
    else:
        filesForm=SubmissionFileFormSet(queryset=SubmissionFile.objects.none())
    return render(request, 'update.html', {'filesForm': filesForm,
                                           'submission': submission})

@login_required
def withdraw(request, subm_id):
    # submission should only be deletable by their creators
    submission = get_object_or_404(Submission, pk=subm_id)
    if request.user not in submission.authors.all():
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
        if request.GET['authmethod']=="hpi":
            return preAuthenticate("http://openid.hpi.uni-potsdam.de", MAIN_URL+"/login?openidreturn")

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
