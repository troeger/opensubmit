'''
    Tets cases focusing on the Assignment model class methods.
'''

from opensubmit.tests.cases import StudentTestCase, SubmitTutorTestCase, SubmitAdminTestCase

class AssignmentModelTutorTestCase(SubmitTutorTestCase):
    def setUp(self):
        super(AssignmentModelTutorTestCase, self).setUp()

    def testScriptUrl(self):
        for ass in [self.openAssignment, self.softDeadlinePassedAssignment,self.hardDeadlinePassedAssignment,self.unpublishedAssignment,self.noHardDeadlineAssignment,self.noGradingAssignment]:
            self.assertIsNone(ass.validity_test_url())
            self.assertIsNone(ass.description_url())
        self.assertIsNotNone(self.validatedAssignment.validity_test_url())

class AssignmentModelAdminTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(AssignmentModelAdminTestCase, self).setUp()

    def testScriptUrl(self):
        for ass in [self.openAssignment, self.softDeadlinePassedAssignment,self.hardDeadlinePassedAssignment,self.unpublishedAssignment,self.noHardDeadlineAssignment,self.noGradingAssignment]:
            self.assertIsNone(ass.validity_test_url())
            self.assertIsNone(ass.description_url())
        self.assertIsNotNone(self.validatedAssignment.validity_test_url())



