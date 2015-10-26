from opensubmit.tests.cases import *

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile


class StudentSubmissionWebTestCase(SubmitTestCase):
    def createSubmissions(self):
        self.openAssignmentSub = self.createSubmission(self.current_user, self.openAssignment)
        self.softDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.hardDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)
        
        self.submissions = (
            self.openAssignmentSub,
            self.softDeadlinePassedAssignmentSub,
            self.hardDeadlinePassedAssignmentSub,
        )


class StudentCreateSubmissionWebTestCase(StudentSubmissionWebTestCase):

    def testCanSubmit(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)
        cases = {
            self.openAssignment: (True, (200, 302, )),
            self.softDeadlinePassedAssignment: (True, (200, 302, )),
            self.hardDeadlinePassedAssignment: (False, (403, )),
            self.unpublishedAssignment: (False, (404, )),
        }
        for assignment in cases:
            response = self.c.post('/assignments/%s/new/' % assignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(submitter.user.pk)
            })
            expect_success, expected_responses = cases[assignment]
            self.assertIn(response.status_code, expected_responses)

            submission_exists = Submission.objects.filter(
                assignment__exact=assignment,
                submitter__exact=submitter.user,
            ).exists()
            self.assertEquals(submission_exists, expect_success)

    def testNonEnrolledCannotSubmit(self):
        submitter = self.not_enrolled_students[0]
        self.loginUser(submitter)
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This submission will fail because the user
                        is not enrolled in the course that the
                        assignment belongs to""",
            'authors': str(submitter.user.pk)
        })
        self.assertEquals(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=submitter.user,
            assignment__exact=self.openAssignment,
        ).count()
        self.assertEquals(submission_count, 0)

    def testCanSubmitAsTeam(self):
        self.loginUser(self.enrolled_students[0])
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.enrolled_students[1].user.pk),
        })
        self.assertIn(response.status_code, (200, 302, ))

        submission = Submission.objects.get(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.openAssignment,
        )
        self.assertTrue(submission.authors.filter(pk__exact=self.enrolled_students[1].user.pk).exists())

    def testCannotSubmitAsTeamWithoutEnrollment(self):
        self.loginUser(self.enrolled_students[0])
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.not_enrolled_students[0].user.pk),
        })
        self.assertEquals(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.openAssignment,
        ).count()
        self.assertEquals(submission_count, 0)

    def testCannotDoubleSubmitThroughTeam(self):
        submitter = self.enrolled_students[1]
        self.loginUser(submitter)
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This is an assignment that student1 has published.""",
            'authors': str(submitter.user.pk)
        })
        self.assertIn(response.status_code, (302, 200, ))

        first_submission_exists = Submission.objects.filter(
            submitter__exact=submitter.user,
            assignment__exact=self.openAssignment,
        ).exists()
        self.assertTrue(first_submission_exists)

        self.loginUser(self.enrolled_students[0])
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.enrolled_students[1].user.pk),
        })
        self.assertEquals(response.status_code, 403)

        submission_exists = Submission.objects.filter(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.openAssignment,
        ).exists()
        self.assertFalse(submission_exists)


class StudentWithdrawSubmissionWebTestCase(StudentSubmissionWebTestCase):
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
                self.assertEquals(submission.state, Submission.WITHDRAWN, submission)
            else:
                self.assertNotEqual(submission.state, Submission.WITHDRAWN, submission)

    def testCannotWithdrawOtherUsers(self):
        self.loginUser(self.enrolled_students[1])
        self.createSubmissions()

        self.loginUser(self.enrolled_students[0])
        cases = {
            self.openAssignmentSub: (False, (403, )),
            self.softDeadlinePassedAssignmentSub: (False, (403, )),
            self.hardDeadlinePassedAssignmentSub: (False, (403, )),
        }
        for submission in cases:
            response = self.c.post('/withdraw/%s/' % submission.pk, {'confirm': '1', })
            expect_submission_withdrawn, expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)
            
            submission = Submission.objects.get(pk__exact=submission.pk)
            if expect_submission_withdrawn:
                self.assertEquals(submission.state, Submission.WITHDRAWN)
            else:
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


class StudentShowSubmissionWebTestCase(StudentSubmissionWebTestCase):
    def testCanSee(self):
        self.loginUser(self.enrolled_students[0])

        self.createSubmissions()
        cases = {
            self.openAssignmentSub: (200, ),
            self.softDeadlinePassedAssignmentSub: (200, ),
            self.hardDeadlinePassedAssignmentSub: (200, ),
        }
        for submission in cases:
            response = self.c.get('/details/%s/' % submission.pk)
            expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)

    def testCannotSeeOtherUsers(self):
        self.loginUser(self.enrolled_students[1])
        self.createSubmissions()

        self.loginUser(self.enrolled_students[0])
        cases = {
            self.openAssignmentSub: (403, ),
            self.softDeadlinePassedAssignmentSub: (403, ),
            self.hardDeadlinePassedAssignmentSub: (403, ),
        }
        for submission in cases:
            response = self.c.get('/details/%s/' % submission.pk)
            expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)