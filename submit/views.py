from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import auth, messages
from openid2rp.django.auth import linkOpenID, preAuthenticate, AX, getOpenIDs
from django.contrib.auth.models import User
from django.core.mail import mail_managers
from django.forms.models import modelformset_factory
from forms import SubmissionForm
from models import SubmissionFile, Submission, Assignment
from django.utils import timezone
import urllib

def index(request):
    if 'logout' in request.GET:
        auth.logout(request)

    if request.user.is_authenticated():
        return redirect('dashboard')

    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

@login_required
def dashboard(request):
    submissions=request.user.submissions.all() | request.user.group_submissions.all()
    submissions=submissions.order_by('-created')
    username=request.user.get_full_name() + " <" + request.user.email + ">"
    assignments=Assignment.open_ones.all()
    return render(request, 'dashboard.html', {
        'submissions': submissions,
        'user': request.user,
        'username': username,
        'assignments': assignments}
    )

@login_required
def new(request):
    SubmissionFileFormSet = modelformset_factory(SubmissionFile, exclude=('submission'))
    if request.POST:
        submissionForm=SubmissionForm(request.POST, request.FILES)
        filesForm=SubmissionFileFormSet(request.POST, request.FILES)
        if submissionForm.is_valid() and filesForm.is_valid():
            submission=submissionForm.save(commit=False)
            submission.submitter=request.user
            submission.save()
            submissionForm.save_m2m()
            files=filesForm.save(commit=False)
            for f in files:
                f.submission=submission
                f.save()
            return redirect('dashboard')
    else:
        submissionForm=SubmissionForm()
        filesForm=SubmissionFileFormSet(queryset=SubmissionFile.objects.none())
    return render(request, 'new.html', {'submissionForm': submissionForm, 'filesForm': filesForm})

@login_required
def withdraw(request, subm_id):
    # submission should only be deletable by their creator
    submission = get_object_or_404(Submission, pk=subm_id, submitter=request.user)
    if "confirm" in request.POST:
        submission.withdrawn=True
        submission.save()
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
            return preAuthenticate("http://openid.hpi.uni-potsdam.de", 'http://%s/login/?openidreturn' % request.get_host())

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
            return redirect('index')

    auth.login(request, user)
    return redirect('dashboard')
