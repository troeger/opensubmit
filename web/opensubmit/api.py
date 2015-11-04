'''
    These are the views being called by the executor. They typically have a different
    security model in comparison to the ordinary views.
'''
from datetime import datetime, timedelta
import os, logging
from time import timezone

logger = logging.getLogger('OpenSubmit')

from django.core.exceptions import PermissionDenied
from django.core.mail import mail_managers
from django.http import HttpResponseForbidden, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from opensubmit import settings
from opensubmit.models import Assignment, Submission, TestMachine, inform_student, SubmissionFile, inform_course_owner


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
            if secret != settings.JOB_EXECUTOR_SECRET:
                raise PermissionDenied
        else:
            if not ass.validity_script_download:
                raise PermissionDenied
        f = ass.attachment_test_validity
        fname = f.name[f.name.rfind('/') + 1:]
    elif filetype == "full_testscript":
        if secret != settings.JOB_EXECUTOR_SECRET:
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
def jobs(request):
    ''' This is the view used by the executor.py scripts for getting / putting the test results.
        Fetching some file for testing is changing the database, so using GET here is not really RESTish. Whatever.
        A visible shared secret in the request is no problem, since the executors come
        from trusted networks. The secret only protects this view from outside foreigners.

        POST requests with 'Action'='get_config' are expected to contain the following parameters:
                    'MachineId',
                    'Config',
                    'Secret',
                    'UUID'

        All other POST requests are expected to contain the following parameters:
                    'SubmissionFileId',
                    'Message',
                    'ErrorCode',
                    'Action',
                    'PerfData',
                    'Secret',
                    'UUID'

        GET requests are expected to contain the following parameters:
                    'Secret',
                    'UUID'

        GET reponses deliver the following elements in the header:
                    'SubmissionFileId',
                    'Timeout',
                    'Action',
                    'PostRunValidation'
    '''
    try:
        if request.method == 'GET':
            secret = request.GET['Secret']
            uuid = request.GET['UUID']
        elif request.method == 'POST':
            secret = request.POST['Secret']
            uuid = request.POST['UUID']
    except Exception as e:
        logger.error("Error finding the neccessary data in the executor request: "+str(e))
        raise PermissionDenied

    if secret != settings.JOB_EXECUTOR_SECRET:
        raise PermissionDenied

    try:
        logger.debug("Test machine is known, updating last contact timestamp")
        machine = TestMachine.objects.get(host=uuid)
        machine.last_contact = datetime.now()
        machine.save()
    except:
        # ask for configuration of new execution hosts by returning the according action
        logger.debug("Test machine is unknown, asking executor for configuration")
        machine = TestMachine(host=uuid, last_contact=datetime.now())
        machine.save()
        response = HttpResponse()
        response['Action'] = 'get_config'
        response['MachineId'] = machine.pk
        return response

    if request.method == "GET":
        subm = Submission.pending_student_tests.filter(assignment__in=machine.assignments.all()).all()
        if len(subm) == 0:
            logger.debug("No pending compile or validation jobs")
            subm = Submission.pending_full_tests.filter(assignment__in=machine.assignments.all()).all()
            if len(subm) == 0:
                logger.debug("No pending full test jobs")
                raise Http404
        for sub in subm:
            logger.debug("Got %u executor jobs"%(len(subm)))
            assert (sub.file_upload)  # must be given when the state model is correct
            if (machine in sub.assignment.test_machines.all()):
                # Machine is a candidate for this job
                fetch_date = sub.get_fetch_date()
                if fetch_date:
                    # This job was already fetched, check how long ago this happened
                    max_delay = timedelta(seconds=sub.assignment.attachment_test_timeout)
                    if fetch_date + max_delay < datetime.now():
                        logger.debug("Resetting executor fetch status for submission %u, due to timeout"%sub.pk)
                        # Stuff that has timed out
                        # we mark it as failed so that the user gets informed
                        # TODO:  Late delivery for such a submission by the executor witll break everything
                        sub.clean_fetch_date()
                        if sub.state == Submission.TEST_COMPILE_PENDING:
                            sub.state = Submission.TEST_COMPILE_FAILED
                            sub.save_compile_result(machine, "Killed due to non-reaction on timeout signals. Please check your application for deadlocks or keyboard input.")
                            inform_student(sub, sub.state)
                        if sub.state == Submission.TEST_VALIDITY_PENDING:
                            sub.save_validation_result(machine, "Killed due to non-reaction on timeout signals. Please check your application for deadlocks or keyboard input.", None)
                            sub.state = Submission.TEST_VALIDITY_FAILED
                            inform_student(sub, sub.state)
                        if sub.state == Submission.TEST_FULL_PENDING:
                            sub.save_fulltest_result(machine, "Killed due to non-reaction on timeout signals. Student not informed, since this was the full test.", None)
                            sub.state = Submission.TEST_FULL_FAILED
                        sub.save()
                        continue
                    else:
                        logger.debug("Submission %u was already fetched, still waiting for it"%sub.pk)
                else:
                    # Requesting machine fits, not fetched so far
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
                        response['PostRunValidation'] = sub.assignment.validity_test_url()
                    elif sub.state == Submission.TEST_FULL_PENDING or sub.state == Submission.CLOSED_TEST_FULL_PENDING:
                        response['Action'] = 'test_full'
                        response['PostRunValidation'] = sub.assignment.full_test_url()
                    else:
                        assert (False)
                    # store date of fetching for determining jobs stucked at the executor
                    sub.save_fetch_date()
                    # 'touch' submission so that it becomes sorted to the end of the queue if something goes wrong
                    sub.modified = datetime.now()
                    sub.save()
                    return response
            else:
                logger.debug("Requesting machine is not responsible for submission %u"%sub.pk)
        # candidate submissions did not fit
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
        perf_data = request.POST['PerfData'].strip()
        submission_file = get_object_or_404(SubmissionFile, pk=sid)
        sub = submission_file.submissions.all()[0]
        error_code = int(request.POST['ErrorCode'])
        if request.POST['Action'] == 'test_compile' and sub.state == Submission.TEST_COMPILE_PENDING:
            sub.save_compile_result(machine, request.POST['Message'])
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
            sub.save_validation_result(machine, request.POST['Message'], perf_data)
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
            sub.save_fulltest_result(machine, request.POST['Message'], perf_data)
            if error_code == 0:
                sub.state = Submission.SUBMITTED_TESTED
                inform_course_owner(request, sub)
            else:
                sub.state = Submission.TEST_FULL_FAILED
                # full tests may be performed several times and are meant to be a silent activity
                # therefore, we send no mail to the student here
        elif request.POST['Action'] == 'test_full' and sub.state == Submission.CLOSED_TEST_FULL_PENDING:
            sub.save_fulltest_result(machine, request.POST['Message'], perf_data)
            sub.state = Submission.CLOSED
            # full tests may be performed several times and are meant to be a silent activity
            # therefore, we send no mail to the student here
        else:
            mail_managers('Warning: Inconsistent job state', str(sub.pk), fail_silently=True)
        sub.clean_fetch_date()
        sub.save()
        return HttpResponse(status=201)


@csrf_exempt
def machines(request):
    ''' This is the view used by the executor.py scripts for putting machine details.
        A visible shared secret in the request is no problem, since the executors come
        from trusted networks. The secret only protects this view from outside foreigners.

        POST requests are expected to contain the following parameters:
                    'Config',
                    'Secret',
                    'UUID'
    '''
    if request.method == "POST":
        print request.POST
        try:
            secret = request.POST['Secret']
            uuid = request.POST['UUID']
            address = request.POST['Address']
        except Exception as e:
            logger.error("Error finding the neccessary data in the executor request: "+str(e))
            raise PermissionDenied

        if secret != settings.JOB_EXECUTOR_SECRET:
            raise PermissionDenied
        try:
            # Find machine database entry for this host
            machine = TestMachine.objects.get(host=uuid)
            machine.last_contact = datetime.now()
            machine.save()
        except:
            # Machine is not known so far, create new record
            machine = TestMachine(host=uuid, address=address, last_contact=datetime.now())
            machine.save()
        # POST request contains all relevant machine information
        machine.config = request.POST['Config']
        machine.save()
        return HttpResponse(status=201)
    else:
        return HttpResponse(status=500)
