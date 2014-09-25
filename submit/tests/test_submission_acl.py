from submit.tests.cases import *

from submit.models import Course, Assignment, Submission
from submit.models import Grading, GradingScheme
from submit.models import UserProfile


class StudentACLTestCase(SubmitTestCase):
    def setUp(self):
        super(StudentACLTestCase, self).setUp()
        self.loginUser(self.enrolled_students[0])

    def createSubmissions(self):
        self.openAssignmentSub = self.createSubmission(self.current_user, self.openAssignment)
        self.softDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.hardDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)
        
        self.submissions = (
            self.openAssignmentSub,
            self.softDeadlinePassedAssignmentSub,
            self.hardDeadlinePassedAssignmentSub,
        )

    def testCanCreateSubmission(self):
        self.assertEquals(self.openAssignment.can_create_submission(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(self.current_user.user), True)
        self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.unpublishedAssignment.can_create_submission(self.current_user.user), False)
        
        for user in (self.admin, self.teacher, self.tutor, ):
            self.assertEquals(self.openAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.unpublishedAssignment.can_create_submission(user.user), True)

    def testCannotDoubleSubmit(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.unpublishedAssignment.can_create_submission(self.current_user.user), False)

    def testCanWithdrawSubmission(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignmentSub.can_withdraw(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), True)
        self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), False)

    def testCanModifySubmission(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignmentSub.can_modify(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignmentSub.can_modify(self.current_user.user), True)
        self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_modify(self.current_user.user), False)

    def testCanReuploadSubmissions(self):
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
                self.assertEquals(self.openAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEquals(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
            else:
                self.assertEquals(self.openAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEquals(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
