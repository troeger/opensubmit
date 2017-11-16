'''
    Tets cases focusing on the frontend withdraw operations of students.
'''

from opensubmit.tests.cases import SubmitTestCase

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile

class StudentWithdrawTestCase(SubmitTestCase):

    def createSubmissions(self):
        self.openAssignmentSub = self.createSubmission(self.current_user, self.openAssignment)
        self.softDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.hardDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)

        self.submissions = (
            self.openAssignmentSub,
            self.softDeadlinePassedAssignmentSub,
            self.hardDeadlinePassedAssignmentSub,
        )

    def testCanWithdraw(self):
        self.loginUser(self.enrolled_students[0])

        self.createSubmissions()
        cases = {
            self.openAssignmentSub: (True, (200, 302, )),
            self.softDeadlinePassedAssignmentSub: (True, (200, 302, )),
            self.hardDeadlinePassedAssignmentSub: (False, (403, )),
        }
        for submission in cases:
            response = self.c.post('/withdraw/%s/' % submission.pk, {'confirm': '1', })
            expect_submission_withdrawn, expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)

            submission = Submission.objects.get(pk__exact=submission.pk)
            if expect_submission_withdrawn:
                self.assertEqual(submission.state, Submission.WITHDRAWN, submission)
            else:
                self.assertNotEqual(submission.state, Submission.WITHDRAWN, submission)

    def testCannotWithdrawOtherUsers(self):
        '''
            Create submissions as one user and check that another user cannot withdraw them.
        '''
        self.loginUser(self.enrolled_students[1])
        self.createSubmissions()

        self.loginUser(self.enrolled_students[0])
        cases = {
            self.openAssignmentSub: 403,
            self.softDeadlinePassedAssignmentSub: 403,
            self.hardDeadlinePassedAssignmentSub: 403,
        }
        for submission in cases:
            response = self.c.post('/withdraw/%s/' % submission.pk, {'confirm': '1', })
            self.assertEqual(response.status_code, cases[submission])
            submission = Submission.objects.get(pk__exact=submission.pk)
            self.assertNotEqual(submission.state, Submission.WITHDRAWN)

    def testCannotWithdrawGraded(self):
        self.loginUser(self.enrolled_students[0])

        for state in (Submission.GRADED, Submission.CLOSED, Submission.CLOSED_TEST_FULL_PENDING, ):
            sub = self.createSubmission(self.current_user, self.openAssignment)
            sub.state = state
            sub.save()

            response = self.c.post('/withdraw/%s/' % sub.pk, {'confirm': '1', })
            self.assertIn(response.status_code, (403, ))
            sub = Submission.objects.get(pk__exact=sub.pk)
            self.assertNotEqual(sub.state, Submission.WITHDRAWN)

    def testCanWithdrawSubmission(self):
        self.loginUser(self.enrolled_students[0])

        self.createSubmissions()
        self.assertEqual(self.openAssignmentSub.can_withdraw(self.current_user.user), True)
        self.assertEqual(self.softDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), True)

    def testCannotWithdrawSubmissionAfterDeadline(self):
        self.loginUser(self.enrolled_students[0])

        self.createSubmissions()
        self.assertEqual(self.hardDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), False)


