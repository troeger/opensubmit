'''
    Tets cases focusing on the Submission model class methods.
'''

from .helpers.submission import create_submission
from .helpers.assignment import *
from .helpers.user import *
from .helpers.course import create_course

from opensubmit.tests.cases import SubmitStudentTestCase
from opensubmit.models import Submission

import os


class SubmissionModel(SubmitStudentTestCase):

    def setUp(self):
        super(SubmissionModel, self).setUp()
        self.admin = create_user(admin_dict)
        self.teacher = create_user(teacher_dict)
        self.tutor = create_user(tutor_dict)
        course = create_course(self.admin)
        grading = create_pass_fail_grading()

        self.open_assignment = create_open_assignment(course, grading)
        self.soft_deadline_passed_assignment = create_soft_passed_assignment(
            course, grading)
        self.hard_deadline_passed_assignment = create_hard_passed_assignment(
            course, grading)
        self.no_hard_assignment = create_no_hard_soft_passed_assignment(
            course, grading)
        self.no_grading_assignment = create_no_grading_assignment(
            course)
        self.unpublished_assignment = create_unpublished_assignment(
            course, grading)

        self.all_assignments = (
            self.open_assignment,
            self.soft_deadline_passed_assignment,
            self.hard_deadline_passed_assignment,
            self.no_hard_assignment,
            self.no_grading_assignment,
            self.unpublished_assignment
        )

        self.open_assignment_sub = create_submission(
            self.user,
            self.open_assignment)
        self.soft_deadline_passed_assignment_sub = create_submission(
            self.user,
            self.soft_deadline_passed_assignment)
        self.hard_deadline_passed_assignment_sub = create_submission(
            self.user,
            self.hard_deadline_passed_assignment)
        self.no_hard_assignment_sub = create_submission(
            self.user,
            self.no_hard_assignment)
        self.no_grading_assignment_sub = create_submission(
            self.user,
            self.no_grading_assignment)
        self.unpublished_assignment_sub = create_submission(
            self.user,
            self.unpublished_assignment)

        self.submissions = (
            self.open_assignment_sub,
            self.soft_deadline_passed_assignment_sub,
            self.hard_deadline_passed_assignment_sub,
            self.no_hard_assignment_sub,
            self.no_grading_assignment_sub,
            self.unpublished_assignment_sub
        )

    def test_info_file_creation(self):
        sub = self.hard_deadline_passed_assignment_sub
        # Info file is opened in write-only mode,
        # so we need the explicit re-opening and deletion here
        info_file = sub.info_file(delete=False)
        info_file.close()
        with open(info_file.name, 'rt', encoding='utf-8') as tmpfile:
            content = tmpfile.read()
        os.remove(info_file.name)
        self.assertIn(sub.submitter.get_full_name(), content)

    def test_can_create_submission(self):
        self.assertEqual(
            self.open_assignment.can_create_submission(
                self.user), True)
        self.assertEqual(
            self.soft_deadline_passed_assignment.can_create_submission(
                self.user), True)

    def test_cannot_create_submission_after_deadline(self):
        self.assertEqual(
            self.hard_deadline_passed_assignment.can_create_submission(
                self.user), False)

    def test_cannot_create_submission_only_soft_passed(self):
        self.assertEqual(
            self.no_hard_assignment.can_create_submission(
                self.user), False)

    def test_can_create_submission_without_grading(self):
        self.assertEqual(
            self.no_grading_assignment.can_create_submission(
                self.user), True)

    def test_cannot_create_submission_before_publishing(self):
        self.assertEqual(
            self.unpublished_assignment.can_create_submission(
                self.user), False)

    def test_admin_teacher_tutor_always_can_create_submission(self):
        for user in (self.admin, self.teacher, self.tutor, ):
            for ass in self.all_assignments:
                self.assertEqual(ass.can_create_submission(user), True)

    def test_cannot_double_submit(self):
        for sub in self.submissions:
            self.assertEqual(sub.assignment.can_create_submission(
                self.user), False)

    def test_can_modify_submission(self):
        self.assertEqual(self.open_assignment_sub.can_modify(
            self.user), True)
        self.assertEqual(self.soft_deadline_passed_assignment_sub.can_modify(
            self.user), True)
        self.assertEqual(self.no_grading_assignment_sub.can_modify(
            self.user), True)
        self.assertEqual(self.no_hard_assignment_sub.can_modify(
            self.user), True)

    def test_cannot_modify_submission_after_deadline(self):
        self.assertEqual(self.hard_deadline_passed_assignment_sub.can_modify(
            self.user), False)

    def test_can_or_cannot_reupload_submissions(self):
        for state, desc in Submission.STATES:
            for submission in self.submissions:
                submission.state = state
                submission.save()

            # Submissions should only be allowed to be re-uploaded if:
            # 1. The code has already been uploaded and executed and
            # 2. the execution has failed, and
            # 3. the hard deadline has not passed.
            if state in (
                Submission.TEST_VALIDITY_FAILED,
                Submission.TEST_FULL_FAILED,
            ):
                self.assertEqual(
                    self.open_assignment_sub.can_reupload(
                        self.user), True)
                self.assertEqual(
                    self.soft_deadline_passed_assignment_sub.can_reupload(
                        self.user), True)
                self.assertEqual(
                    self.hard_deadline_passed_assignment_sub.can_reupload(
                        self.user), False)
            else:
                self.assertEqual(
                    self.open_assignment_sub.can_reupload(
                        self.user), False)
                self.assertEqual(
                    self.soft_deadline_passed_assignment_sub.can_reupload(
                        self.user), False)
                self.assertEqual(
                    self.hard_deadline_passed_assignment_sub.can_reupload(
                        self.user), False)
