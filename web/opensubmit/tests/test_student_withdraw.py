'''
    Tets cases focusing on the frontend withdraw operations of students.
'''

from opensubmit.models import Submission
from opensubmit.tests.cases import SubmitStudentScenarioTestCase
from .helpers.user import get_student_dict
from .helpers.submission import create_submission


class StudentWithdraw(SubmitStudentScenarioTestCase):

    def test_can_withdraw(self):
        self.create_submissions()
        cases = {
            self.open_assignment_sub: (True, (200, 302, )),
            self.soft_deadline_passed_assignment_sub: (True, (200, 302, )),
            self.hard_deadline_passed_assignment_sub: (False, (403, )),
        }
        for submission in cases:
            response = self.c.post('/withdraw/%s/'
                                   % submission.pk, {'confirm': '1', })
            expect_submission_withdrawn, expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)

            submission = Submission.objects.get(pk__exact=submission.pk)
            if expect_submission_withdrawn:
                self.assertEqual(submission.state,
                                 Submission.WITHDRAWN, submission)
            else:
                self.assertNotEqual(
                    submission.state, Submission.WITHDRAWN, submission)

    def test_cannot_withdraw_other_users(self):
        '''
            Create submissions as one user and check
            that another user cannot withdraw them.
        '''
        self.create_submissions()

        self.create_and_login_user(get_student_dict(1))
        cases = {
            self.open_assignment_sub: 403,
            self.soft_deadline_passed_assignment_sub: 403,
            self.hard_deadline_passed_assignment_sub: 403,
        }
        for submission in cases:
            response = self.c.post('/withdraw/%s/' %
                                   submission.pk, {'confirm': '1', })
            self.assertEqual(response.status_code, cases[submission])
            submission = Submission.objects.get(pk__exact=submission.pk)
            self.assertNotEqual(submission.state, Submission.WITHDRAWN)

    def test_cannot_withdraw_graded(self):
        for state in (Submission.GRADED,
                      Submission.CLOSED,
                      Submission.CLOSED_TEST_FULL_PENDING):
            sub = create_submission(self.user, self.open_assignment)
            sub.state = state
            sub.save()

            response = self.c.post('/withdraw/%s/' %
                                   sub.pk, {'confirm': '1', })
            self.assertIn(response.status_code, (403, ))
            sub = Submission.objects.get(pk__exact=sub.pk)
            self.assertNotEqual(sub.state, Submission.WITHDRAWN)

    def testCanWithdrawSubmission(self):
        self.create_submissions()
        self.assertEqual(
            self.open_assignment_sub.can_withdraw(self.user), True)
        self.assertEqual(
            self.soft_deadline_passed_assignment_sub.can_withdraw(
                self.user), True)

    def testCannotWithdrawSubmissionAfterDeadline(self):
        self.create_submissions()
        self.assertEqual(
            self.hard_deadline_passed_assignment_sub.can_withdraw(
                self.user), False)
