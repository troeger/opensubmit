'''
    Test cases focusing on the Assignment model class methods.
'''

from opensubmit.tests.cases import SubmitTutorTestCase, SubmitAdminTestCase

from .helpers.course import create_course
from .helpers.assignment import create_pass_fail_grading
from .helpers.assignment import create_non_validated_assignments
from .helpers.assignment import create_validated_assignment_with_file


class AssignmentModelTutorTestCase(SubmitTutorTestCase):
    def setUp(self):
        super(AssignmentModelTutorTestCase, self).setUp()
        self.course = create_course(self.user)
        self.grading_scheme = create_pass_fail_grading()

    def test_script_url(self):
        assignments = create_non_validated_assignments(self.course,
                                                       self.grading_scheme)
        v_ass = create_validated_assignment_with_file(self.course,
                                                      self.grading_scheme)

        for ass in assignments:
            self.assertIsNone(ass.validity_test_url_relative())
        self.assertIsNotNone(v_ass.validity_test_url_relative())


class AssignmentModelAdminTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(AssignmentModelAdminTestCase, self).setUp()
        self.course = create_course(self.user)
        self.grading_scheme = create_pass_fail_grading()

    def test_script_url(self):
        assignments = create_non_validated_assignments(
            self.course, self.grading_scheme)
        v_ass = create_validated_assignment_with_file(self.course,
                                                      self.grading_scheme)

        for ass in assignments:
            self.assertIsNone(ass.validity_test_url_relative())
        self.assertIsNotNone(v_ass.validity_test_url_relative())
