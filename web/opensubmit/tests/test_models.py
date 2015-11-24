'''
    Test cases for specific model functions that are difficult to test in larger context.
'''

from opensubmit.tests.cases import StudentTestCase, SubmitTutorTestCase, SubmitAdminTestCase

class AssignmentModelStudentTestCase(StudentTestCase):
    def setUp(self):
        super(AssignmentModelStudentTestCase, self).setUp()

class AssignmentModelTutorTestCase(SubmitTutorTestCase):
    def setUp(self):
        super(AssignmentModelTutorTestCase, self).setUp()

class AssignmentModelAdminTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(AssignmentModelAdminTestCase, self).setUp()




