import os

from django.test import LiveServerTestCase
from django.test.utils import override_settings
from opensubmit.tests.cases import StudentTestCase
from django.contrib.auth.models import User

from opensubmit.models import TestMachine

@override_settings(DEBUG=True)	# otherwise we have no traceback from live server
class ExecutorTestCase(StudentTestCase, LiveServerTestCase):
    def setUp(self):
        super(ExecutorTestCase, self).setUp()
        self.val_sub = self.createValidatedSubmission(self.current_user)

    def testRegisterExecutorExplicit(self):
    	machine_count = TestMachine.objects.all().count()
    	exit_status = os.system("python3 jobexec/executor.py register opensubmit/tests/executor.cfg")
    	self.assertEquals(0, exit_status)
    	self.assertEquals(machine_count+1, TestMachine.objects.all().count())

