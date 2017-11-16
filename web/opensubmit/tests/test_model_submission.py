'''
    Tets cases focusing on the Submission model class methods.
'''

from opensubmit.tests.cases import SubmitTestCase, rootdir

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile

import os

class ModelSubmissionTestCase(SubmitTestCase):

    def createSubmissions(self):
        self.openAssignmentSub = self.createSubmission(self.current_user, self.openAssignment)
        self.softDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.hardDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)
        self.noHardDeadlineAssignmentSub = self.createSubmission(self.current_user, self.noHardDeadlineAssignment)
        self.noGradingAssignmentSub = self.createSubmission(self.current_user, self.noGradingAssignment)

        self.submissions = (
            self.openAssignmentSub,
            self.softDeadlinePassedAssignmentSub,
            self.hardDeadlinePassedAssignmentSub,
            self.noHardDeadlineAssignmentSub,
            self.noGradingAssignmentSub
        )

    def testInfoFileCreation(self):
        self.loginUser(self.enrolled_students[0])
        sub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)
        # Info file is opened in write-only mode, so we need the explicit re-opening and deletion here
        info_file=sub.info_file(delete=False)
        info_file.close()
        with open(info_file.name, 'rt') as tmpfile:
            content=tmpfile.read()
        os.remove(info_file.name)
        self.assertIn(sub.submitter.get_full_name(), content)

    def testCanCreateSubmission(self):
        self.loginUser(self.enrolled_students[0])
        self.assertEqual(self.openAssignment.can_create_submission(self.current_user.user), True)
        self.assertEqual(self.softDeadlinePassedAssignment.can_create_submission(self.current_user.user), True)

    def testCannotCreateSubmissionAfterDeadline(self):
        self.loginUser(self.enrolled_students[0])
        self.assertEqual(self.hardDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)

    def testCanCreateSubmissionWithoutHardDeadline(self):
        self.loginUser(self.enrolled_students[0])
        self.assertEqual(self.noHardDeadlineAssignment.can_create_submission(self.current_user.user), True)

    def testCanCreateSubmissionWithoutGrading(self):
        self.loginUser(self.enrolled_students[0])
        self.assertEqual(self.noGradingAssignment.can_create_submission(self.current_user.user), True)

    def testCannotCreateSubmissionBeforePublishing(self):
        self.loginUser(self.enrolled_students[0])
        self.assertEqual(self.unpublishedAssignment.can_create_submission(self.current_user.user), False)

    def testAdminTeacherTutorAlwaysCanCreateSubmission(self):
        for user in (self.admin, self.teacher, self.tutor, ):
            for ass in self.allAssignments:
                self.assertEqual(ass.can_create_submission(user.user), True)

    def testCannotDoubleSubmit(self):
        self.loginUser(self.enrolled_students[0])
        self.createSubmissions()
        for sub in self.submissions:
            self.assertEqual(sub.assignment.can_create_submission(self.current_user.user), False)

    def testCanModifySubmission(self):
        self.loginUser(self.enrolled_students[0])
        self.createSubmissions()
        self.assertEqual(self.openAssignmentSub.can_modify(self.current_user.user), True)
        self.assertEqual(self.softDeadlinePassedAssignmentSub.can_modify(self.current_user.user), True)
        self.assertEqual(self.noGradingAssignmentSub.can_modify(self.current_user.user), True)
        self.assertEqual(self.noHardDeadlineAssignmentSub.can_modify(self.current_user.user), True)

    def testCannotModifySubmissionAfterDeadline(self):
        self.loginUser(self.enrolled_students[0])
        self.createSubmissions()
        self.assertEqual(self.hardDeadlinePassedAssignmentSub.can_modify(self.current_user.user), False)

    def testCanOrCannotReuploadSubmissions(self):
        self.loginUser(self.enrolled_students[0])
        self.createSubmissions()
        for state, desc in Submission.STATES:
            for submission in self.submissions:
                submission.state = state
                submission.save()

            # Submissions should only be allowed to be re-uploaded if:
            # 1. The code has already been uploaded and executed and
            # 2. the execution has failed, and
            # 3. the hard deadline has not passed.
            if state in (
                Submission.TEST_COMPILE_FAILED,
                Submission.TEST_VALIDITY_FAILED,
                Submission.TEST_FULL_FAILED,
            ):
                self.assertEqual(self.openAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEqual(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEqual(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
            else:
                self.assertEqual(self.openAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEqual(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEqual(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)

