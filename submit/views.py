from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import auth, messages
from openid2rp.django.auth import linkOpenID, preAuthenticate, AX, getOpenIDs
from django.contrib.auth.models import User
from django.core.mail import mail_managers
from django.forms.models import modelformset_factory
from forms import SubmissionWithGroupsForm, SubmissionWithoutGroupsForm
from models import SubmissionFile, Submission, Assignment
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
import urllib
from settings import JOB_EXECUTOR_SECRET

def index(request):
    if request.user.is_authenticated():
        return redirect('dashboard')

    return render(request, 'index.html')

def logout(request):
    auth.logout(request)
    return redirect('index')

def about(request):
    return render(request, 'about.html')

@csrf_exempt
def jobs(request, secret):
    # This is the view used by the executor.py scripts for getting / putting the test results.
    #
    # Fetching some file for testing is changing the database, so using GET here is not really RESTish. Anyway.
    #
    # A visible shared secret in the request is no problem, since the executors come
    # from trusted networks. The secret only protects this view from outside foreigners.
    if secret != JOB_EXECUTOR_SECRET:
        raise PermissionDenied
    if request.method == "GET":
        # Hand over a pending job to be tested as file download
        # Return the oldest submisison in status UNTESTED
        subm = Submission.objects.filter(state=Submission.UNTESTED).order_by('-created')
        if len(subm) == 0:
            raise Http404
        for sub in subm:
            files=sub.active_files()
            if files:
                frecord=files[0]
                f=frecord.attachment
                fname=f.name[f.name.rfind('/')+1:]
                response=HttpResponse(f, content_type='application/binary')
                response['Content-Disposition'] = 'attachment; filename="%s"'%fname
                response['SubmissionFileId'] = str(frecord.pk)
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
        if int(submission_file.error_code) == 0:
            subm.state = Submission.SUBMITTED_TESTED
        else:
            subm.state = Submission.TEST_FAILED
        subm.save()
        return HttpResponse(status=201)

@login_required
def dashboard(request):
    authored=request.user.authored.order_by('-created')
    username=request.user.get_full_name() + " <" + request.user.email + ">"
    waiting_for_action=[subm.assignment for subm in request.user.authored.all().exclude(state=Submission.WITHDRAWN)]
    openassignments=[ass for ass in Assignment.open_ones.all() if ass not in waiting_for_action]
    return render(request, 'dashboard.html', {
        'authored': authored,
        'user': request.user,
        'username': username,
        'assignments': openassignments}
    )

@login_required
def new(request, ass_id):
    ass = get_object_or_404(Assignment, pk=ass_id)
    if ass.course.max_authors > 1:
        SubmissionForm=SubmissionWithGroupsForm
    else:
        SubmissionForm=SubmissionWithoutGroupsForm
    # Files are a separate model entity -> separate form
    SubmissionFileFormSet = modelformset_factory(SubmissionFile, exclude=('submission', 'fetched', 'output', 'error_code', 'replaced_by'))
    if request.POST:
        submissionForm=SubmissionForm(request.POST, request.FILES)
        submissionForm.removeFinishedAuthors(ass)
        filesForm=SubmissionFileFormSet(request.POST, request.FILES)
        if submissionForm.is_valid() and filesForm.is_valid():
            submission=submissionForm.save(commit=False)   # to set submitter
            submission.submitter=request.user
            submission.assignment=ass
            if submission.assignment.test_attachment:
                submission.state=Submission.UNTESTED
            else:
                submission.state=Submission.SUBMITTED
            submission.save()
            submission.authors.add(request.user)    # submitter is always an author
            submissionForm.save_m2m()   # because of commit=False
            files=filesForm.save(commit=False)
            for f in files:
                f.submission=submission
                f.save()
            return redirect('dashboard')
    else:
        submissionForm=SubmissionForm()
        submissionForm.removeFinishedAuthors(ass)
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
    SubmissionFileFormSet = modelformset_factory(SubmissionFile, exclude=('submission', 'fetched', 'output', 'error_code', 'replaced_by'))
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
            submission.state = Submission.UNTESTED
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
            return preAuthenticate("http://openid.hpi.uni-potsdam.de", 'http://%s/%s/?openidreturn' % (request.get_host(), reverse('login')))

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
                email = unicode(user_sreg['email'],'utf-8')[:29]

            if AX.email in user_ax:
                email = unicode(user_ax[AX.email],'utf-8')[:29]

            # no username given, register user with his e-mail address as username
            if not user_name and email:
                new_user = User(username=email, email=email)

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
