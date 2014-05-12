'''
    These are the views being called by the executor. They typically have a different
    security model in comparison to the ordinary views.
'''
import datetime
import os
from time import timezone

from django.core.exceptions import PermissionDenied
from django.core.mail import mail_managers
from django.http import HttpResponseForbidden, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from submit.settings import JOB_EXECUTOR_SECRET, MAIN_URL
from submit.models import Assignment, Submission, TestMachine, inform_student, SubmissionFile, inform_course_owner


def download(request, obj_id, filetype, secret=None):
    ''' 
    Download facilility for files on the server.
    This view is intentionally not login-protected, since the
    security happens on a more fine-grained level:
    - A requestor who wants a submission attachment or grading notes must be author 
     (student front page) or staff (correctors).
    - A requestor who wants a validation script gets it with a secret (executor script)
      or if public download is enabled for it.
    '''
    if filetype == "attachment":
        subm = get_object_or_404(Submission, pk=obj_id)
        if not (request.user in subm.authors.all() or request.user.is_staff):
            return HttpResponseForbidden()
        f = subm.file_upload.attachment
        fname = subm.file_upload.basename()
    elif filetype == "grading_file":
        subm = get_object_or_404(Submission, pk=obj_id)
        if not (request.user in subm.authors.all() or request.user.is_staff):
            return HttpResponseForbidden()
        f = subm.grading_file
        fname = os.path.basename(subm.grading_file.name)
    elif filetype == "validity_testscript":
        ass = get_object_or_404(Assignment, pk=obj_id)
        if secret:
            if secret != JOB_EXECUTOR_SECRET:
                raise PermissionDenied
        else:
            if not ass.validity_script_download:
                raise PermissionDenied
        f = ass.attachment_test_validity
        fname = f.name[f.name.rfind('/') + 1:]
    elif filetype == "full_testscript":
        if secret != JOB_EXECUTOR_SECRET:
            raise PermissionDenied
        ass = get_object_or_404(Assignment, pk=obj_id)
        f = ass.attachment_test_full
        fname = f.name[f.name.rfind('/') + 1:]
    else:
        raise Http404
    response = HttpResponse(f, content_type='application/binary')
    response['Content-Disposition'] = 'attachment; filename="%s"' % fname
    return response


@csrf_exempt
def jobs(request, secret):
    ''' This is the view used by the executor.py scripts for getting / putting the test results.
        Fetching some file for testing is changing the database, so using GET here is not really RESTish. Whatever.
        A visible shared secret in the request is no problem, since the executors come
        from trusted networks. The secret only protects this view from outside foreigners.
    '''
    if secret != JOB_EXECUTOR_SECRET:
        raise PermissionDenied
    if request.method == "GET":
        try:
            machine = TestMachine.objects.get(host=request.get_host())
            machine.last_contact = datetime.now()
            machine.save()
        except:
            # ask for configuration of new execution hosts by returning the according action
            machine = TestMachine(host=request.get_host(), last_contact=datetime.now())
            machine.save()
            response = HttpResponse()
            response['Action'] = 'get_config'
            response['MachineId'] = machine.pk
            return response
        subm = Submission.pending_student_tests.all()
        if len(subm) == 0:
            subm = Submission.pending_full_tests.all()
            if len(subm) == 0:
                raise Http404
        for sub in subm:
            assert (sub.file_upload)  # must be given when the state model is correct
            # only deliver jobs that are unfetched so far, or where the executor should have finished meanwhile
            # it may happen in special cases that stucked executors deliver their result after the timeout
            # this is not really a problem, since the result remains the same for the same file
            #TODO: Make this a part of the original query
            #TODO: Count number of attempts to leave the same state, mark as finally failed in case; alternatively, the executor must always deliver a re.
            if (not sub.file_upload.fetched) or (sub.file_upload.fetched + datetime.timedelta(
                    seconds=sub.assignment.attachment_test_timeout) < timezone.now()):
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
                f = sub.file_upload.attachment
                # on dev server, we sometimes have stale database entries
                if not os.access(f.path, os.F_OK):
                    mail_managers('Warning: Missing file',
                                  'Missing file on storage for submission file entry %u: %s' % (
                                      sub.file_upload.pk, str(sub.file_upload.attachment)), fail_silently=True)
                    continue
                response = HttpResponse(f, content_type='application/binary')
                response['Content-Disposition'] = 'attachment; filename="%s"' % sub.file_upload.basename()
                response['SubmissionFileId'] = str(sub.file_upload.pk)
                response['Timeout'] = sub.assignment.attachment_test_timeout
                if sub.state == Submission.TEST_COMPILE_PENDING:
                    response['Action'] = 'test_compile'
                elif sub.state == Submission.TEST_VALIDITY_PENDING:
                    response['Action'] = 'test_validity'
                    # reverse() is messing up here when we have to FORCE_SCRIPT case, so we do manual URL construction
                    response['PostRunValidation'] = MAIN_URL + "/download/%u/validity_testscript/secret=%s" % (
                        sub.assignment.pk, JOB_EXECUTOR_SECRET)
                elif sub.state == Submission.TEST_FULL_PENDING or sub.state == Submission.CLOSED_TEST_FULL_PENDING:
                    response['Action'] = 'test_full'
                    # reverse() is messing up here when we have to FORCE_SCRIPT case, so we do manual URL construction
                    response['PostRunValidation'] = MAIN_URL + "/download/%u/full_testscript/secret=%s" % (
                        sub.assignment.pk, JOB_EXECUTOR_SECRET)
                else:
                    assert (False)
                # store date of fetching for determining jobs stucked at the executor
                sub.file_upload.fetched = timezone.now()
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
        submission_file = get_object_or_404(SubmissionFile, pk=sid)
        sub = submission_file.submissions.all()[0]
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
        submission_file.fetched = None  # makes the file fetchable again by executors, but now in a different state
        perf_data = request.POST['PerfData'].strip()
        if perf_data != "":
            submission_file.perf_data = perf_data
        else:
            submission_file.perf_data = None
        submission_file.save()
        sub.save()
        return HttpResponse(status=201)


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
