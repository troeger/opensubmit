'''
    Test cases for the executor code.

    Note the neccessary python search path manipulation below.

Missing tests:

  - Makefile in validator package should override student Makefile

'''

import os
import time
import os.path
import sys
import logging

from django.core import mail
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from opensubmit.tests.cases import SubmitStudentScenarioTestCase
from django.core.urlresolvers import reverse

from opensubmit.models import TestMachine, SubmissionTestResult, Submission
from opensubmit.tests import utils

from .helpers.submission import create_validatable_submission
from .helpers.submission import create_validated_submission
from .helpers.djangofiles import create_submission_file
from .helpers.user import create_user, get_student_dict

sys.path.insert(0, os.path.dirname(__file__) + '/../../../executor/')
# pyflakes: disable=E402
from opensubmitexec import config, cmdline, server

logger = logging.getLogger('opensubmitexec')


class Validation(TestCase):
    '''
    Tests for the execution of validation scripts by the executor.
    '''

    def setUp(self):
        super(Validation, self).setUp()
        self.config = config.read_config(
            os.path.dirname(__file__) + "/executor.cfg")

    def _test_validation_case(self, directory):
        '''
        Each of the validator.py files uses the Python assert()
        statement to check by itself if the result is the expected
        one for its case.
        '''
        base_dir = os.path.dirname(__file__) + '/submfiles/validation/'
        cmdline.copy_and_run(self.config, base_dir + directory)

    def test_0100fff(self):
        self._test_validation_case('0100fff')

    def test_0100tff(self):
        self._test_validation_case('0100tff')

    def test_0100ttf(self):
        self._test_validation_case('0100ttf')

    def test_1000fff(self):
        self._test_validation_case('1000fff')

    def test_1000fft(self):
        self._test_validation_case('1000fft')

    def test_1000tff(self):
        self._test_validation_case('1000tff')

    def test_1000tft(self):
        self._test_validation_case('1000tft')

    def test_1000ttf(self):
        self._test_validation_case('1000ttf')

    def test_1000ttt(self):
        self._test_validation_case('1000ttt')

    def test_1010tff(self):
        self._test_validation_case('1010tff')

    def test_1010ttf(self):
        self._test_validation_case('1010ttf')

    def test_1100tff(self):
        self._test_validation_case('1100tff')

    def test_1100ttf(self):
        self._test_validation_case('1100ttf')

    def test_3000tff(self):
        self._test_validation_case('3000tff')

    def test_3000ttf(self):
        self._test_validation_case('3000ttf')

    def test_3010tff(self):
        self._test_validation_case('3010tff')

    def test_3010ttf(self):
        self._test_validation_case('3010ttf')

    def test_b000tff(self):
        self._test_validation_case('b000tff')

    def test_b010tff(self):
        self._test_validation_case('b010tff')


class Communication(SubmitStudentScenarioTestCase):
    '''
    Tests for the communication of the executor with the OpenSubmit server.
    '''

    def setUp(self):
        settings.MAIN_URL = self.live_server_url
        super(Communication, self).setUp()
        self.config = config.read_config(
            os.path.dirname(__file__) + "/executor.cfg",
            override_url=self.live_server_url)

    def _register_executor(self):
        server.send_hostinfo(self.config)
        return TestMachine.objects.order_by('-last_contact')[0]

    def _run_executor(self):
        return cmdline.download_and_run(self.config)

    def _register_test_machine(self):
        '''
        Utility step for a common test case preparation:
        - Create validatable submission
        - Register a test machine for it
        '''
        sf = create_submission_file()
        sub = create_validatable_submission(
            self.user, self.validated_assignment, sf)
        test_machine = self._register_executor()
        sub.assignment.test_machines.add(test_machine)
        return sub

    def test_subprocess_exception(self):
        '''
        Test reaction when the executor crashes internally.
        '''
        sub = self._register_test_machine()

        self.config['Execution']['script_runner'] = 'efergää4'
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
        self.assertEqual(machine_count + 1, TestMachine.objects.all().count())

    @override_settings(JOB_EXECUTOR_SECRET='foo')
    def test_invalid_secret(self):
        self.assertNotEqual(True, self._run_executor())

    def test_everything_already_tested(self):
        create_validated_submission(self.user, self.validated_assignment)
        assert(self._register_executor().pk)
        self.assertEqual(False, self._run_executor())

    def test_parallel_executors_test(self):
        NUM_PARALLEL = 3
        self.validated_assignment.test_machines.add(self._register_executor())
        subs = []
        for i in range(1, NUM_PARALLEL + 1):
            stud = create_user(get_student_dict(i))
            self.course.participants.add(stud.profile)
            self.course.save()
            sf = create_submission_file()
            subs.append(create_validatable_submission(
                stud, self.validated_assignment, sf))

        # Span a number of threads, each triggering the executor
        # This only creates a real test case if executor serialization
        # is off (see tests/executor.cfg)
        return_codes = utils.run_parallel(len(subs), self._run_executor)
        self.assertEqual(
            len(list(filter((lambda x: x is True), return_codes))),
            len(subs))

        for sub in subs:
            results = SubmissionTestResult.objects.filter(
                submission_file=sub.file_upload,
                kind=SubmissionTestResult.VALIDITY_TEST
            )
            self.assertEqual(NUM_PARALLEL, len(results))
            self.assertNotEqual(0, len(results[0].result))

    def test_too_long_validation(self):
        sub = self._register_test_machine()

        # set very short timeout
        sub.assignment.attachment_test_timeout = 1
        sub.assignment.save()
        # mock that this submission was already fetched for validation,
        # and the result never returned
        sub.save_fetch_date()
        # wait for the timeout
        time.sleep(2)
        # Fire up the executor, should mark the submission as timed out
        self.assertEqual(True, self._run_executor())
        # Check if timeout marking took place
        sub.refresh_from_db()
        self.assertEqual(sub.state, Submission.TEST_VALIDITY_FAILED)
        assert("timeout" in sub.get_validation_result().result)

    def test_too_long_full_test(self):
        sub = self._register_test_machine()

        # perform validation step
        self.assertEqual(True, self._run_executor())
        # set very short timeout
        sub.assignment.attachment_test_timeout = 1
        sub.assignment.save()
        # mock that this submission was already fetched for full test,
        # and the result never returned
        sub.save_fetch_date()
        # wait for the timeout
        time.sleep(2)
        # Fire up the executor, should mark the submission as timed out
        self.assertEqual(None, self._run_executor())
        # Check if timeout marking took place
        sub.refresh_from_db()
        self.assertEqual(sub.state, Submission.TEST_FULL_FAILED)
        assert("timeout" in sub.get_fulltest_result().result)

    def test_single_file_validator_test(self):
        sub = self._register_test_machine()

        self.assertEqual(True, self._run_executor())
        results = SubmissionTestResult.objects.filter(
            submission_file=sub.file_upload,
            kind=SubmissionTestResult.VALIDITY_TEST
        )
        self.assertEqual(1, len(results))

        # compile
        self.sub = self.createValidatableNoArchiveSubmission(self.current_user)
        self.sub.assignment.attachment_test_compile = False
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
        sub = self._register_test_machine()
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
        sf = create_submission_file()
        self.sub = create_validatable_submission(
            self.user, self.validated_assignment, sf)
        test_machine = self._register_executor()
        self.sub.assignment.test_machines.add(test_machine)
        self.sub.state = Submission.TEST_FULL_PENDING
        self.sub.save()
        post_data = {'Secret': settings.JOB_EXECUTOR_SECRET,
                     'UUID': test_machine.host,
                     'Action': 'test_compile',
                     'SubmissionFileId': self.sub.file_upload.pk,
                     'PerfData': '',
                     'ErrorCode': 0,
                     'Message': 'In A Bottle'}
        self.c.post(reverse('jobs'), post_data)
        self.assertNotEqual(len(mail.outbox), 0)
        self.assertIn('Action reported by the executor: test_compile',
                      mail.outbox[0].message().as_string())

    def test_assignment_specific_test_machine(self):
        # Register two test machines T1 and T2
        real_machine = self._register_executor()
        fake_machine = TestMachine(host="127.0.0.2")
        fake_machine.save()
        # Assign each of them to a different assignment
        self.open_assignment.test_machines.add(real_machine)
        self.validated_assignment.test_machines.add(fake_machine)
        # Produce submission for the assignment linked to fake_machine
        sub1 = Submission(
            assignment=self.validated_assignment,
            submitter=self.user,
            state=Submission.TEST_VALIDITY_PENDING,
            file_upload=create_submission_file()
        )
        sub1.save()
        # Run real_machine executor, should not react on this submission
        old_sub1_state = sub1.state
        self.assertEqual(False, self._run_executor())
        # Make sure that submission object was not touched,
        # whatever the executor says
        sub1 = Submission.objects.get(pk=sub1.pk)
        self.assertEqual(old_sub1_state, sub1.state)
