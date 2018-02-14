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

API_VERSION = '2.0.0'




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


@method_decorator(csrf_exempt, name='dispatch')
class JobsView(View):
    '''
    This is the view used by the executor.py scripts
    for getting / putting the test results.

    TODO: Make it a real API, based on some framework.
    TODO: Factor out state model from this method.
    '''
    http_method_names = ['get', 'post']

    def _check_data(self, expected, data):
        for name in expected:
            if name not in data:
                raise PermissionDenied
            if name == 'Secret':
                self.secret = data['Secret']
                if self.secret != settings.JOB_EXECUTOR_SECRET:
                    raise PermissionDenied
            if name == 'UUID':
                self.uuid = data['UUID']
            if name == 'Action':
                self.action = data['Action']
            if name == 'Message':
                self.message = data['Message']
            if name == 'MessageTutor':
                self.message_tutor = data['MessageTutor']
            if name == 'ErrorCode':
                self.error_code = data['ErrorCode']

    def _clean_submissions(self):
        '''
        Clean up submissions where the answer from the executors took too long.
        '''
        pending_submissions = Submission.pending_tests.filter(
            file_upload__fetched__isnull=False)
        for sub in pending_submissions:
            max_delay = timedelta(
                seconds=sub.assignment.attachment_test_timeout)
            # There is a small chance that meanwhile the result was delivered, so fetched became NULL
            if sub.file_upload.fetched and sub.file_upload.fetched + max_delay < datetime.now():
                logger.debug(
                    "Resetting executor fetch status for submission %u, due to timeout" % sub.pk)
                # TODO:  Late delivery for such a submission by the executor may lead to result overwriting. Check this.
                sub.clean_fetch_date()
                machine = sub.assignment.test_machines.all()[0]
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

    def _determine_machine(self):
        '''
        Determine the machine entry, based on the provided UUID,
        and sets self.machine accordingly.
        '''
        assert(self.uuid)
        try:
            self.machine = TestMachine.objects.get(host=self.uuid)
            if not self.machine.enabled:
                # Act like no jobs are given
                raise Http404
            self.machine.last_contact = datetime.now()
            self.machine.save()
        except Exception:
            self.machine = None

    def _job_response(self, sub):
        '''
        Create a HTTP response with the given submission as job.
        '''
        f = sub.file_upload.attachment
        # on dev server, we sometimes have stale database entries
        if not os.access(f.path, os.F_OK):
            mail_managers('Warning: Missing file',
                          'Missing file on storage for submission file entry %u: %s' % (
                              sub.file_upload.pk, str(sub.file_upload.attachment)), fail_silently=True)
            raise Http404
        # Adjust last modification date
        sub.save_fetch_date()
        sub.modified = datetime.now()
        sub.save()
        # Create response object
        response = HttpResponse(f, content_type='application/binary')
        response['APIVersion'] = API_VERSION  # semantic versioning
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

    def get(self, request):
        '''
        Get a new job.
        '''
        self._check_data(['Secret', 'UUID'], request.GET)
        # Determine originating machine
        self._determine_machine()
        if not self.machine:
            # ask for configuration of new execution hosts by returning the according action
            logger.debug(
                "Test machine is unknown, creating entry and asking executor for configuration.")
            response = HttpResponse()
            response['Action'] = 'get_config'
            response['APIVersion'] = API_VERSION  # semantic versioning
            return response

        # Now get an appropriate submission.
        self._clean_submissions()
        submissions = Submission.pending_tests
        submissions = submissions.filter(assignment__in=self.machine.assignments.all()) \
                                 .filter(file_upload__isnull=False) \
                                 .filter(file_upload__fetched__isnull=True)
        if len(submissions) == 0:
            raise Http404
        else:
            sub = submissions[0]
        return self._job_response(sub)

    def _get_config_action_response(self, request):
        self._check_data(['Config'], request.POST)
        # See if this machine is already registered
        self._determine_machine()
        if not self.machine:
            # Create machine entry
            self.machine = TestMachine(host=self.uuid, config=request.POST['Config'])
            self.machine.save()
            return HttpResponse(status=201)
        else:
            # Should not happen
            raise Http404

    def _save_validation_result(self, sub):
        assert(self.machine)
        assert(self.message)
        assert(self.message_tutor)
        sub.save_validation_result(
            self.machine, self.message, self.message_tutor)
        if self.error_code == 0:
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

    def _save_full_result(self, sub):
        assert(self.machine)
        assert(self.message_tutor)
        sub.save_fulltest_result(
            self.machine, self.message_tutor)
        if self.error_code == 0:
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

    def _save_full_result_again(self, sub):
        assert(self.machine)
        assert(self.message_tutor)
        logger.debug(
            "Closed full test done, setting state to closed again")
        sub.save_fulltest_result(
            self.machine, self.message_tutor)
        sub.state = Submission.CLOSED
        # full tests may be performed several times and are meant to be a silent activity
        # therefore, we send no mail to the student here

    def post(self, request):
        self._check_data(['Secret', 'UUID', 'Action'], request.POST)

        if self.action == 'get_config':
            return self._get_config_action_response()

        self._check_data(['SubmissionFileId', 'ErrorCode', 'Message', 'MessageTutor'], request.POST)
        sid = request.POST['SubmissionFileId']
        error_code = int(request.POST['ErrorCode'])
        submission_file = get_object_or_404(SubmissionFile, pk=sid)
        sub = submission_file.submissions.all()[0]
        self._determine_machine()
        logger.debug("Storing executor results for submission %u" % (sub.pk))
        # Job state: Waiting for validity test
        # Possible with + without full test
        # Possible with + without grading
        if self.action == 'test_validity' and sub.state == Submission.TEST_VALIDITY_PENDING:
            self._save_validation_result(sub)
        # Job state: Waiting for full test
        # Possible with + without grading
        elif self.action == 'test_full' and sub.state == Submission.TEST_FULL_PENDING:
            self._save_full_result(sub)
        # Job state: Waiting for full test of already closed jobs ("re-test")
        # Grading is already done
        elif self.action == 'test_full' and sub.state == Submission.CLOSED_TEST_FULL_PENDING:
            self._save_full_result_again(sub)
        # Job state: Validity test already failed
        # Can happen if the validation is set to failed due to timeout,
        # but the executor delivers the late result.
        # Happens in reality only with >= 2 executors,
        # since the second one is pulling for new jobs and triggers
        # the timeout check while the first one is still stucked with the big job.
        # Can be ignored.
        elif self.action == 'test_validity' and sub.state == Submission.TEST_VALIDITY_FAILED:
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
                Student message from the executor: %s
                Tutor message from the executor: %s
                Error code from the executor: %u
                ''' % (sub.pk, submission_file.pk, self.action,
                       sub.state_for_tutors(), sub.state,
                       self.message, self.message_tutor, error_code)
            mail_managers('Warning: Inconsistent job state',
                          msg, fail_silently=True)
        # Mark work as done
        sub.save()
        sub.clean_fetch_date()
        return HttpResponse(status=201)
