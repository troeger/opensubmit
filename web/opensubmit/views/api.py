'''
    These are the views being called by the executor.
    They security currently relies on a provided shared secret.

    We therefore assume that executors come from a trusted network.
'''

from datetime import datetime, timedelta
import os

from django.core.exceptions import PermissionDenied
from django.core.mail import mail_managers
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, View
from django.utils.decorators import method_decorator

from opensubmit import settings
from opensubmit.models import Assignment, Submission, TestMachine, SubmissionFile
from opensubmit.mails import inform_student
from opensubmit.views.helpers import BinaryDownloadMixin

import logging
logger = logging.getLogger('OpenSubmit')


class ValidityScriptView(BinaryDownloadMixin, DetailView):
    '''
    Download of validity test script for an assignment.
    '''
    model = Assignment

    def get_object(self, queryset=None):
        ass = super().get_object(queryset)
        if 'secret' in self.kwargs:
            if self.kwargs['secret'] != settings.JOB_EXECUTOR_SECRET:
                raise PermissionDenied
        else:
            if not ass.validity_script_download:
                raise PermissionDenied
        self.f = ass.attachment_test_validity
        self.fname = self.f.name[self.f.name.rfind('/') + 1:]
        return ass


class FullScriptView(BinaryDownloadMixin, DetailView):
    '''
    Download of full test script for an assignment.
    '''
    model = Assignment

    def get_object(self, queryset=None):
        ass = super().get_object(queryset)
        if self.kwargs['secret'] != settings.JOB_EXECUTOR_SECRET:
            raise PermissionDenied
        self.f = ass.attachment_test_full
        self.fname = self.f.name[self.f.name.rfind('/') + 1:]
        return ass


@method_decorator(csrf_exempt, name='dispatch')
class MachinesView(View):
    '''
    View for sending details about an executor machine,

    POST requests are expected to contain the following parameters:
                'Config',
                'Secret',
                'UUID'

    TODO: Change to a DetailView would demand to have the uuid
    in the URL as pk. Demands an incompatible change in the executor protocol.
    '''
    http_method_names = ['post']

    def post(self, request):
        if self.request.POST['Secret'] != settings.JOB_EXECUTOR_SECRET:
            raise PermissionDenied
        machine, created = TestMachine.objects.get_or_create(host=request.POST['UUID'])
        machine.last_contact = datetime.now()
        machine.config = request.POST['Config']
        machine.save()
        return HttpResponse(status=201)


@csrf_exempt
def jobs(request):
    ''' This is the view used by the executor.py scripts for getting / putting the test results.
        Fetching some file for testing is changing the database, so using GET here is not really RESTish. Whatever.
        A visible shared secret in the request is no problem, since the executors come
        from trusted networks. The secret only protects this view from outside foreigners.

        TODO: Make it a real API, based on some framework.
        TODO: Factor out state model from this method into some model.

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
        logger.error(
            "Error finding the neccessary data in the executor request: " + str(e))
        raise PermissionDenied

    if secret != settings.JOB_EXECUTOR_SECRET:
        raise PermissionDenied

    # Update last_contact information for test machine
    machine, created = TestMachine.objects.update_or_create(
        host=uuid, defaults={'last_contact': datetime.now()})
    if created:
        # ask for configuration of new execution hosts by returning the according action
        logger.debug(
            "Test machine is unknown, creating entry and asking executor for configuration.")
        response = HttpResponse()
        response['Action'] = 'get_config'
        response['APIVersion'] = '1.0.0'  # semantic versioning
        response['MachineId'] = machine.pk
        return response

    if not machine.enabled:
        # Act like no jobs are given for him
        raise Http404

    if request.method == "GET":
        # Clean up submissions where the answer from the executors took too long
        pending_submissions = Submission.pending_tests.filter(
            file_upload__fetched__isnull=False)
        #logger.debug("%u pending submission(s)"%(len(pending_submissions)))
        for sub in pending_submissions:
            max_delay = timedelta(
                seconds=sub.assignment.attachment_test_timeout)
            # There is a small chance that meanwhile the result was delivered, so fetched became NULL
            if sub.file_upload.fetched and sub.file_upload.fetched + max_delay < datetime.now():
                logger.debug(
                    "Resetting executor fetch status for submission %u, due to timeout" % sub.pk)
                # TODO:  Late delivery for such a submission by the executor may lead to result overwriting. Check this.
                sub.clean_fetch_date()
                if sub.state == Submission.TEST_VALIDITY_PENDING:
                    sub.save_validation_result(
                        machine, "Killed due to non-reaction. Please check your application for deadlocks or keyboard input.", "Killed due to non-reaction on timeout signals.")
                    sub.state = Submission.TEST_VALIDITY_FAILED
                    sub.inform_student(sub.state)
                if sub.state == Submission.TEST_FULL_PENDING:
                    sub.save_fulltest_result(
                        machine, "Killed due to non-reaction on timeout signals. Student not informed, since this was the full test.")
                    sub.state = Submission.TEST_FULL_FAILED
                sub.save()

        # Now get an appropriate submission.
        submissions = Submission.pending_tests
        submissions = submissions.filter(assignment__in=machine.assignments.all()) \
                                 .filter(file_upload__isnull=False) \
                                 .filter(file_upload__fetched__isnull=True)
        if len(submissions) == 0:
            # Nothing found to be fetchable
            #logger.debug("No pending work for executors")
            raise Http404
        else:
            sub = submissions[0]
        sub.save_fetch_date()
        sub.modified = datetime.now()
        sub.save()

        # create HTTP response with file download
        f = sub.file_upload.attachment
        # on dev server, we sometimes have stale database entries
        if not os.access(f.path, os.F_OK):
            mail_managers('Warning: Missing file',
                          'Missing file on storage for submission file entry %u: %s' % (
                              sub.file_upload.pk, str(sub.file_upload.attachment)), fail_silently=True)
            raise Http404
        response = HttpResponse(f, content_type='application/binary')
        response['APIVersion'] = '1.0.0'  # semantic versioning
        response['Content-Disposition'] = 'attachment; filename="%s"' % sub.file_upload.basename()
        response['SubmissionFileId'] = str(sub.file_upload.pk)
        response['SubmissionOriginalFilename'] = sub.file_upload.original_filename
        response['SubmissionId'] = str(sub.pk)
        response['SubmitterName'] = sub.submitter.get_full_name()
        response['SubmitterStudentId'] = sub.submitter.profile.student_id
        response['AuthorNames'] = sub.authors.all()
        response['SubmitterStudyProgram'] = str(sub.submitter.profile.study_program)
        response['Course'] = str(sub.assignment.course)
        response['Assignment'] = str(sub.assignment)
        response['Timeout'] = sub.assignment.attachment_test_timeout
        if sub.state == Submission.TEST_VALIDITY_PENDING:
            response['Action'] = 'test_validity'
            response['PostRunValidation'] = sub.assignment.validity_test_url()
        elif sub.state == Submission.TEST_FULL_PENDING or sub.state == Submission.CLOSED_TEST_FULL_PENDING:
            response['Action'] = 'test_full'
            response['PostRunValidation'] = sub.assignment.full_test_url()
        else:
            assert (False)
        logger.debug("Delivering submission %u as new %s job" %
                     (sub.pk, response['Action']))
        return response

    elif request.method == "POST":
        # first check if this is just configuration data, and not a job result
        if request.POST['Action'] == 'get_config':
            machine = TestMachine.objects.get(
                pk=int(request.POST['MachineId']))
            machine.config = request.POST['Config']
            machine.save()
            return HttpResponse(status=201)

        # executor.py is providing the results as POST parameters
        sid = request.POST['SubmissionFileId']
        submission_file = get_object_or_404(SubmissionFile, pk=sid)
        sub = submission_file.submissions.all()[0]
        logger.debug("Storing executor results for submission %u" % (sub.pk))
        error_code = int(request.POST['ErrorCode'])
        # Job state: Waiting for validity test
        # Possible with + without full test
        # Possible with + without grading
        if request.POST['Action'] == 'test_validity' and sub.state == Submission.TEST_VALIDITY_PENDING:
            sub.save_validation_result(
                machine, request.POST['Message'], request.POST['MessageTutor'])
            if error_code == 0:
                # We have a full test
                if sub.assignment.attachment_test_full:
                    logger.debug(
                        "Validity test working, setting state to pending full test")
                    sub.state = Submission.TEST_FULL_PENDING
                # We have no full test
                else:
                    logger.debug(
                        "Validity test working, setting state to tested")
                    sub.state = Submission.SUBMITTED_TESTED
                    if not sub.assignment.is_graded():
                        # Assignment is not graded. We are done here.
                        sub.state = Submission.CLOSED
                        sub.inform_student(Submission.CLOSED)
            else:
                logger.debug(
                    "Validity test not working, setting state to failed")
                sub.state = Submission.TEST_VALIDITY_FAILED
            sub.inform_student(sub.state)
        # Job state: Waiting for full test
        # Possible with + without grading
        elif request.POST['Action'] == 'test_full' and sub.state == Submission.TEST_FULL_PENDING:
            sub.save_fulltest_result(
                machine, request.POST['MessageTutor'])
            if error_code == 0:
                if sub.assignment.is_graded():
                    logger.debug("Full test working, setting state to tested (since graded)")
                    sub.state = Submission.SUBMITTED_TESTED
                else:
                    logger.debug("Full test working, setting state to closed (since not graded)")
                    sub.state = Submission.CLOSED
                    inform_student(sub, Submission.CLOSED)
            else:
                logger.debug("Full test not working, setting state to failed")
                sub.state = Submission.TEST_FULL_FAILED
                # full tests may be performed several times and are meant to be a silent activity
                # therefore, we send no mail to the student here
        # Job state: Waiting for full test of already closed jobs ("re-test")
        # Grading is already done
        elif request.POST['Action'] == 'test_full' and sub.state == Submission.CLOSED_TEST_FULL_PENDING:
            logger.debug(
                "Closed full test done, setting state to closed again")
            sub.save_fulltest_result(
                machine, request.POST['MessageTutor'])
            sub.state = Submission.CLOSED
            # full tests may be performed several times and are meant to be a silent activity
            # therefore, we send no mail to the student here
        elif request.POST['Action'] == 'test_validity' and sub.state == Submission.TEST_VALIDITY_FAILED:
            # Can happen if the validation is set to failed due to timeout, but the executor delivers the late result.
            # Happens in reality only with >= 2 executors, since the second one is pulling for new jobs and triggers
            # the timeout check while the first one is still stucked with the big job.
            # Can be ignored.
            logger.debug(
                "Ignoring executor result, since the submission is already marked as failed.")
        else:
            msg = '''
                Dear OpenSubmit administrator,

                the executors returned some result, but this does not fit to the current submission state.
                This is a strong indication for a bug in OpenSubmit - sorry for that.
                The system will ignore the report from executor and mark the job as to be repeated.
                Please report this on the project GitHub page for further investigation.

                Submission ID: %u
                Submission File ID reported by the executor: %u
                Action reported by the executor: %s
                Current state of the submission: %s (%s)
                Message from the executor: %s
                Error code from the executor: %u
                ''' % (sub.pk, submission_file.pk, request.POST['Action'],
                       sub.state_for_tutors(), sub.state,
                       request.POST['Message'], error_code)
            mail_managers('Warning: Inconsistent job state',
                          msg, fail_silently=True)
        # Mark work as done
        sub.save()
        sub.clean_fetch_date()
        return HttpResponse(status=201)

