'''
    Test cases for the executor code.

    Note the neccessary python search path manipulation below.
'''

import os, time

from django.core import mail
from django.test import LiveServerTestCase
from django.test.utils import override_settings, skipUnless
from opensubmit.tests.cases import StudentTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from opensubmit.models import TestMachine, SubmissionTestResult, Submission
from opensubmit.tests import utils
from opensubmit import settings

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../executor/opensubmit' ))
import executor

class ExecutorTestCase(StudentTestCase, LiveServerTestCase):

    def setUp(self):
        super(ExecutorTestCase, self).setUp()

    def _registerExecutor(self):
        executor.send_config(os.path.dirname(__file__)+"/executor.cfg")
        return TestMachine.objects.order_by('-last_contact')[0]

    def _runExecutor(self):
        return executor.run(os.path.dirname(__file__)+"/executor.cfg")

    def testRegisterExecutorExplicit(self):
        machine_count = TestMachine.objects.all().count()
        assert(self._registerExecutor().pk)
        self.assertEquals(machine_count+1, TestMachine.objects.all().count())

    def testRunRequestFromUnknownMachine(self):
        # This is expected to trigger a register action request from the server
        self.assertNotEquals(True, self._runExecutor())

    @override_settings(JOB_EXECUTOR_SECRET='foo')
    def testInvalidSecret(self):
        self.assertNotEquals(True, self._runExecutor())

    def testEverythingAlreadyTested(self):
        self.createValidatedSubmission(self.current_user)
        assert(self._registerExecutor().pk)
        self.assertEquals(False, self._runExecutor())

    def testCompileTest(self):
        self.sub = self.createValidatableSubmission(self.current_user) 
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(True, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.COMPILE_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))

    def testBrokenCompileTest(self):
        self.sub = self.createCompileBrokenSubmission(self.current_user) 
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(False, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.COMPILE_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))
        print str(results[0].result)

    def testCompileWithSupportFilesTest(self):
        self.sub = self.createValidatableWithSupportFilesSubmission(self.current_user)
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(True, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.COMPILE_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))


    def testParallelExecutorsCompileTest(self):
        self.sub = self.createValidatableSubmission(self.current_user)
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)

        # Span a number of threads, each triggering the executor
        # This only creates a real test case if executor serialization is off (see tests/executor.cfg)
        NUM_THREADS = 70
        return_codes = utils.run_parallel(NUM_THREADS, self._runExecutor)
        # Compile + validation + full test makes 3 expected successful runs
        self.assertEquals(len(filter((lambda x: x is True),  return_codes)), 3)
        self.assertEquals(len(filter((lambda x: x is False), return_codes)), NUM_THREADS-3)

        # Make sure that compilation result is given
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.COMPILE_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))


    def testTooLongCompile(self):
        self.sub = self.createValidatableSubmission(self.current_user)
        # set very short timeout
        self.sub.assignment.attachment_test_timeout=1
        self.sub.assignment.save()
        # mock that this submission was already fetched for compilation, and the result never returned
        self.sub.save_fetch_date()
        # wait for the timeout
        time.sleep(2)
        # Fire up the executor, should mark the submission as timed out
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(False, self._runExecutor())       # No job is available
        # Check if timeout marking took place
        self.sub.refresh_from_db()
        self.assertEquals(self.sub.state, Submission.TEST_COMPILE_FAILED)
        assert("timeout" in self.sub.get_compile_result().result)

    def testTooLongValidation(self):
        self.sub = self.createValidatableSubmission(self.current_user)
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        # perform compilation step
        self.assertEquals(True, self._runExecutor())
        # set very short timeout
        self.sub.assignment.attachment_test_timeout=1
        self.sub.assignment.save()
        # mock that this submission was already fetched for validation, and the result never returned
        self.sub.save_fetch_date()
        # wait for the timeout
        time.sleep(2)
        # Fire up the executor, should mark the submission as timed out
        self.assertEquals(False, self._runExecutor())       # No job is available
        # Check if timeout marking took place
        self.sub.refresh_from_db()
        self.assertEquals(self.sub.state, Submission.TEST_VALIDITY_FAILED)
        assert("timeout" in self.sub.get_validation_result().result)

    def testTooLongFullTest(self):
        self.sub = self.createValidatableSubmission(self.current_user)
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        # perform compilation step
        self.assertEquals(True, self._runExecutor())
        # perform validation step
        self.assertEquals(True, self._runExecutor())
        # set very short timeout
        self.sub.assignment.attachment_test_timeout=1
        self.sub.assignment.save()
        # mock that this submission was already fetched for full test, and the result never returned
        self.sub.save_fetch_date()
        # wait for the timeout
        time.sleep(2)
        # Fire up the executor, should mark the submission as timed out
        self.assertEquals(False, self._runExecutor())       # No job is available
        # Check if timeout marking took place
        self.sub.refresh_from_db()
        self.assertEquals(self.sub.state, Submission.TEST_FULL_FAILED)
        assert("timeout" in self.sub.get_fulltest_result().result)


    def testValidationTest(self):
        # compile
        self.sub = self.createValidatableSubmission(self.current_user)
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(True, self._runExecutor())
        # validate
        self.assertEquals(True, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))

    def testSingleFileValidatorTest(self):
        # compile
        self.sub = self.createSingleFileValidatorSubmission(self.current_user)
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(True, self._runExecutor())
        # validate
        self.assertEquals(True, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))

    def testValidationWithSupportFilesTest(self):
        # compile
        self.sub = self.createValidatableWithSupportFilesSubmission(self.current_user)
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(True, self._runExecutor())
        # validate
        self.assertEquals(True, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))

    def testValidationTestWithoutCompilation(self):
        # compile
        self.sub = self.createValidatableNoArchiveSubmission(self.current_user)
        self.sub.assignment.attachment_test_compile=False
        self.sub.assignment.save()
        test_machine = self._registerExecutor()
        self.sub.assignment.test_machines.add(test_machine)
        self.assertEquals(True, self._runExecutor())
        # validate
        self.assertEquals(True, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))


    def testFullTest(self):
        # We need a fully working validation run beforehand
        self.testValidationTest()
        self.assertEquals(True, self._runExecutor())
        results = SubmissionTestResult.objects.filter(
            submission_file=self.sub.file_upload,
            kind=SubmissionTestResult.FULL_TEST
        )
        self.assertEquals(1, len(results))
        self.assertNotEquals(0, len(results[0].result))

    def testInconsistentStateEMail(self):
        '''
            Test operator email on inconsistent state.
            Since executor execution and submission sending is one step,
            we need to mock the incoming invalid executor request.
        '''
        self.sub = self.createValidatableSubmission(self.current_user)
        test_machine = self._registerExecutor()
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

    def testAssignmentSpecificTestMachine(self):
        # Register two test machines T1 and T2
        real_machine = self._registerExecutor()
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
        self.assertEquals(False, self._runExecutor())
        # Make sure that submission object was not touched, whatever the executor says
        sub1 = Submission.objects.get(pk=sub1.pk)
        self.assertEquals(old_sub1_state, sub1.state)

