'''
    Tets cases focusing on the Assignment model class methods.
'''

from opensubmit.tests.cases import StudentTestCase, SubmitTutorTestCase, SubmitAdminTestCase

class AssignmentModelTutorTestCase(SubmitTutorTestCase):
    def setUp(self):
        super(AssignmentModelTutorTestCase, self).setUp()

    def testScriptUrl(self):
        self.assertIsNone(self.openAssignment.validity_test_url())
        self.assertIsNotNone(self.validatedAssignment.validity_test_url())
        self.assertIsNone(self.softDeadlinePassedAssignment.validity_test_url())
        self.assertIsNone(self.hardDeadlinePassedAssignment.validity_test_url())
        self.assertIsNone(self.unpublishedAssignment.validity_test_url())
        self.assertIsNone(self.noHardDeadlineAssignment.validity_test_url())
        self.assertIsNone(self.noGradingAssignment.validity_test_url())

class AssignmentModelAdminTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(AssignmentModelAdminTestCase, self).setUp()

    def testScriptUrl(self):
        self.assertIsNone(self.openAssignment.validity_test_url())
        self.assertIsNotNone(self.validatedAssignment.validity_test_url())
        self.assertIsNone(self.softDeadlinePassedAssignment.validity_test_url())
        self.assertIsNone(self.hardDeadlinePassedAssignment.validity_test_url())
        self.assertIsNone(self.unpublishedAssignment.validity_test_url())
        self.assertIsNone(self.noHardDeadlineAssignment.validity_test_url())
        self.assertIsNone(self.noGradingAssignment.validity_test_url())



