'''
    Tets cases focusing on the Course model class methods.
'''

from opensubmit.models import Submission
from opensubmit.tests.cases import StudentTestCase, SubmitTutorTestCase, SubmitAdminTestCase

class CourseModelStudentTestCase(StudentTestCase):
    def setUp(self):
        super(CourseModelStudentTestCase, self).setUp()

    def testGradableSubmissionsList(self):
        # Expected number of results when the submission has that state
        expected = (
            (0, Submission.RECEIVED),
            (0, Submission.WITHDRAWN),
            (1, Submission.SUBMITTED),
            (0, Submission.TEST_COMPILE_PENDING),
            (0, Submission.TEST_COMPILE_FAILED),
            (0, Submission.TEST_VALIDITY_PENDING),
            (0, Submission.TEST_VALIDITY_FAILED),
            (0, Submission.TEST_FULL_PENDING),
            (1, Submission.TEST_FULL_FAILED),
            (1, Submission.SUBMITTED_TESTED),
            (1, Submission.GRADING_IN_PROGRESS),
            (0, Submission.GRADED),
            (0, Submission.CLOSED),
            (0, Submission.CLOSED_TEST_FULL_PENDING))

        # Course without submissions should not have gradable submissions
        qs = self.course.gradable_submissions()
        self.assertEquals(qs.count(), 0)

        for count, state in expected:
            sub = self.createSubmission(self.current_user, self.openAssignment)
            sub.state = state
            sub.save()
            self.assertEquals(qs.count(), count, "Submission count for state %s is incorrect."%state)

    def testGradedSubmissionsList(self):
        # Expected number of results when the submission has that state
        expected = (
            (0, Submission.RECEIVED),
            (0, Submission.WITHDRAWN),
            (0, Submission.SUBMITTED),
            (0, Submission.TEST_COMPILE_PENDING),
            (0, Submission.TEST_COMPILE_FAILED),
            (0, Submission.TEST_VALIDITY_PENDING),
            (0, Submission.TEST_VALIDITY_FAILED),
            (0, Submission.TEST_FULL_PENDING),
            (0, Submission.TEST_FULL_FAILED),
            (0, Submission.SUBMITTED_TESTED),
            (0, Submission.GRADING_IN_PROGRESS),
            (1, Submission.GRADED),
            (0, Submission.CLOSED),
            (0, Submission.CLOSED_TEST_FULL_PENDING))

        # Course without submissions should not have gradable submissions
        qs = self.course.graded_submissions()
        self.assertEquals(qs.count(), 0)

        for count, state in expected:
            sub = self.createSubmission(self.current_user, self.openAssignment)
            sub.state = state
            sub.save()
            self.assertEquals(qs.count(), count, "Submission count for state %s is incorrect."%state)

    def testCourseAuthors(self):
        # Course without submissions should have no authors
        qs = self.course.authors()
        self.assertEquals(qs.count(), 0)

        sub = self.createSubmission(self.current_user, self.openAssignment)
        self.assertEquals(qs.count(), len(sub.authors.all()))

