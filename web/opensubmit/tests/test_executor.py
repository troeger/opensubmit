'''
    Test cases for the executor code.

    Note the neccessary python search path manipulation below.
'''

import os
import time
import os.path
import sys

from django.core import mail
from django.test import LiveServerTestCase
from django.test.utils import override_settings, skipUnless
from opensubmit.tests.cases import StudentTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from opensubmit.models import TestMachine, SubmissionTestResult, Submission
from opensubmit.tests import utils
from opensubmit import settings

sys.path.insert(0, os.path.dirname(__file__)+'/../../../executor/')
import opensubmitexec

class Validation(TestCase):
    '''
    Tests for the execution of validation scripts by the executor.
    '''
    def setUp(self):
        super(Validation, self).setUp()
        self.config = opensubmitexec.config.read_config(os.path.dirname(__file__)+"/executor.cfg")

    def test_all(self):
        '''
        Go through all cases in ./submfiles/validation and run them.
        Each of the validator.py files uses the Python assert() statement to check
        by itself if the result is the expected one for its case.
        '''
        base_dir = os.path.dirname(__file__)+'/submfiles/validation/'

        for root, dirs, files in os.walk(base_dir):
            for directory in dirs:
                cmdline.copy_and_run(self.config, root+directory)


class Communication(StudentTestCase, LiveServerTestCase):
    '''
    Tests for the communication of the executor with the OpenSubmit server.
    '''
    def setUp(self):
        super(Communication, self).setUp()
        self.config = opensubmitexec.config.read_config(
                        os.path.dirname(__file__)+"/executor.cfg",
                        override_url=self.live_server_url)

    def _register_executor(self):
        opensubmitexec.server.send_hostinfo(self.config)
        return TestMachine.objects.order_by('-last_contact')[0]

    def _run_executor(self):
        return opensubmitexec.cmdline.download_and_run(self.config)

    def _register_and_compile(self):
        '''
        Utility step for a common test case preparation:
        - Create validatable submission
        - Register a test machine for it
        - Run the compile step
        '''
        sub = self.createValidatableSubmission(self.current_user) 
        test_machine = self._register_executor()
        sub.assignment.test_machines.add(test_machine)
        # Compile, should work
        self.assertEqual(True, self._run_executor())
        return sub

    def test_subprocess_exception(self):
        '''
        Test reaction when the executor crashes internally.
        '''
        sub = self._register_and_compile()

        self.config['Execution']['script_runner']='efergää4'
        # Validation, should fail now
        self.assertEqual(False, self._run_executor())
        result = SubmissionTestResult.objects.get(
            submission_file=sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertIn('FileNotFoundError', result.result)

    def test_register_executor_explicit(self):
        machine_count = TestMachine.objects.all().count()
        assert(self._register_executor().pk)
        self.assertEqual(machine_count+1, TestMachine.objects.all().count())

    @override_settings(JOB_EXECUTOR_SECRET='foo')
    def test_invalid_secret(self):
        self.assertNotEqual(True, self._run_executor())

    def test_everything_already_tested(self):
        self.createValidatedSubmission(self.current_user)
        assert(self._register_executor().pk)
        self.assertEqual(None, self._run_executor())

    def test_compile_test(self):
        sub = self._register_and_compile()

        results = SubmissionTestResult.objects.filter(
            submission_file=sub.file_upload,
            kind=SubmissionTestResult.COMPILE_TEST
        )
        self.assertEqual(1, len(results))
        self.assertNotEqual(0, len(results[0].result))

    def test_broken_compile_test(self):
        self.sub = self.createCompileBrokenSubmission(self.current_user) 
        test_machine = self._register_executor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEqual(False, self._run_executor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.COMPILE_TEST
        )
        self.assertEqual(1, len(results))
        self.assertNotEqual(0, len(results[0].result))
        self.assertNotEqual(None, self.sub.get_compile_result())
        # Integrate another test here, which relates to teacher backend submission status rendering
        # This is bad style - @TODO Refactor tests to make executor runs a helper function for all test classes
        from opensubmit.admin.submission import SubmissionAdmin
        sa=SubmissionAdmin(Submission, None)
        self.assertNotEqual(None, sa.compile_result(self.sub))
        self.assertEqual("Enabled, no results.", sa.validation_result(self.sub))
        self.assertEqual("Enabled, no results.", sa.fulltest_result(self.sub))

    def test_parallel_executors_compile_test(self):
        self.validatedAssignment.test_machines.add(self._register_executor())
        num_students=len(self.enrolled_students)
        subs=[self.createValidatableSubmission(stud) for stud in self.enrolled_students]
        # Span a number of threads, each triggering the executor
        # This only creates a real test case if executor serialization is off (see tests/executor.cfg)
        return_codes = utils.run_parallel(num_students, self._runExecutor)
        # Compile + validation + full test makes 3 expected successful runs
        self.assertEqual(len(list(filter((lambda x: x is True),  return_codes))), num_students)

        # Make sure that compilation result is given
        for sub in subs:
            results = SubmissionTestResult.objects.filter(
                submission_file=sub.file_upload,
                kind=SubmissionTestResult.COMPILE_TEST
            )
            self.assertEqual(1, len(results))
            self.assertNotEqual(0, len(results[0].result))

    def test_too_long_validation(self):
        sub = self._register_and_compile()

        # set very short timeout
        sub.assignment.attachment_test_timeout=1
        sub.assignment.save()
        # mock that this submission was already fetched for validation, and the result never returned
        sub.save_fetch_date()
        # wait for the timeout
        time.sleep(2)
        # Fire up the executor, should mark the submission as timed out
        self.assertEqual(None, self._run_executor())       # No job is available
        # Check if timeout marking took place
        sub.refresh_from_db()
        self.assertEqual(sub.state, Submission.TEST_VALIDITY_FAILED)
        assert("timeout" in sub.get_validation_result().result)

    def test_too_long_fulltest(self):
        sub = self._register_and_compile()

        # perform validation step
        self.assertEqual(True, self._run_executor())
        # set very short timeout
        sub.assignment.attachment_test_timeout=1
        sub.assignment.save()
        # mock that this submission was already fetched for full test, and the result never returned
        sub.save_fetch_date()
        # wait for the timeout
        time.sleep(2)
        # Fire up the executor, should mark the submission as timed out
        self.assertEqual(None, self._run_executor())       # No job is available
        # Check if timeout marking took place
        sub.refresh_from_db()
        self.assertEqual(sub.state, Submission.TEST_FULL_FAILED)
        assert("timeout" in sub.get_fulltest_result().result)

    def test_single_file_validator(self):
        sub = self._register_and_compile()

        self.assertEqual(True, self._run_executor())
        results = SubmissionTestResult.objects.filter(
            submission_file=sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertEqual(1, len(results))
        self.assertNotEqual(0, len(results[0].result))v
 
    def test_validation_without_compilation(self):
        # compile
        self.sub = self.createValidatableNoArchiveSubmission(self.current_user)
        self.sub.assignment.attachment_test_compile=False
        self.sub.assignment.save()
        test_machine = self._register_executor()
        self.sub.assignment.test_machines.add(test_machine)
        # validate
        self.assertEqual(True, self._run_executor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertEqual(1, len(results))
        self.assertNotEqual(0, len(results[0].result))


    def test_full_test(self):
        sub = self._register_and_compile()
        # validation test
        self.assertEqual(True, self._run_executor())
        # full test
        self.assertEqual(True, self._run_executor())
        results = SubmissionTestResult.objects.filter(
            submission_file=sub.file_upload,
            kind=SubmissionTestResult.FULL_TEST
        )
        self.assertEqual(1, len(results))
        self.assertNotEqual(0, len(results[0].result))

    def test_inconsistent_state_email(self):
        '''
            Test operator email on inconsistent state.
            Since executor execution and submission sending is one step,
            we need to mock the incoming invalid executor request.
        '''
        self.sub = self.createValidatableSubmission(self.current_user)
        test_machine = self._register_executor()
        self.sub.assignment.test_machines.add(test_machine)
        self.sub.state = Submission.TEST_FULL_PENDING
        self.sub.save()
        post_data = {   'Secret': settings.JOB_EXECUTOR_SECRET,
                        'UUID': test_machine.host,
                        'Action': 'test_compile',
                        'SubmissionFileId': self.sub.file_upload.pk,
                        'PerfData': '',
                        'ErrorCode': 0,
                        'Message': 'In A Bottle'}
        response = self.c.post(reverse('jobs'),post_data)
        self.assertNotEqual(len(mail.outbox), 0)
        self.assertIn('Action reported by the executor: test_compile', mail.outbox[0].message().as_string())

    def test_assignment_specific_test_machine(self):
        # Register two test machines T1 and T2
        real_machine = self._register_executor()
        fake_machine = TestMachine(host="127.0.0.2")
        fake_machine.save()
        # Assign each of them to a different assignment
        self.openAssignment.test_machines.add(real_machine)
        self.validatedAssignment.test_machines.add(fake_machine)
        # Produce submission for the assignment linked to fake_machine
        sub1 = Submission(
            assignment=self.validatedAssignment,
            submitter=self.current_user.user,
            state=Submission.TEST_COMPILE_PENDING,
            file_upload=self.createSubmissionFile()
        )
        sub1.save()
        # Run real_machine executor, should not react on this submission
        old_sub1_state = sub1.state
        self.assertEqual(None, self._run_executor())
        # Make sure that submission object was not touched, whatever the executor says
        sub1 = Submission.objects.get(pk=sub1.pk)
        self.assertEqual(old_sub1_state, sub1.state)

