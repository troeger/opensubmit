'''
    Tets cases focusing on the Course model class methods.
'''

from .helpers.course import create_course
from .helpers.assignment import create_pass_fail_grading
from .helpers.assignment import create_open_assignment
from .helpers.submission import create_submission


from opensubmit.models import Submission
from opensubmit.tests.cases import SubmitStudentTestCase


class CourseModelStudentTestCase(SubmitStudentTestCase):
    def setUp(self):
        super(CourseModelStudentTestCase, self).setUp()
        self.course = create_course(self.user)
        grading = create_pass_fail_grading()
        self.assignment = create_open_assignment(self.course, grading)

    def test_gradable_submissions_list(self):
        # Expected number of results when the submission has that state
        expected = (
            (0, Submission.RECEIVED),
            (0, Submission.WITHDRAWN),
            (1, Submission.SUBMITTED),
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
        self.assertEqual(qs.count(), 0)

        for count, state in expected:
            sub = create_submission(self.user, self.assignment)
            sub.state = state
            sub.save()
            self.assertEqual(
                qs.count(), count,
                "Submission count for state %s is incorrect." % state)

    def testGradedSubmissionsList(self):
        # Expected number of results when the submission has that state
        expected = (
            (0, Submission.RECEIVED),
            (0, Submission.WITHDRAWN),
            (0, Submission.SUBMITTED),
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
        self.assertEqual(qs.count(), 0)

        for count, state in expected:
            sub = create_submission(self.user, self.assignment)
            sub.state = state
            sub.save()
            self.assertEqual(
                qs.count(), count,
                "Submission count for state %s is incorrect." % state)

    def testCourseAuthors(self):
        # Course without submissions should have no authors
        qs = self.course.authors()
        self.assertEqual(qs.count(), 0)

        sub = create_submission(self.user, self.assignment)
        self.assertEqual(qs.count(), len(sub.authors.all()))
