import os

from django.test import LiveServerTestCase
from django.test.utils import override_settings, skipUnless
from opensubmit.tests.cases import StudentTestCase
from django.contrib.auth.models import User

from opensubmit.models import TestMachine, SubmissionTestResult, Submission

from opensubmit import executor

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

    def testValidationTest(self):
        # We need a fully working compile run beforehand
        self.testCompileTest()
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

