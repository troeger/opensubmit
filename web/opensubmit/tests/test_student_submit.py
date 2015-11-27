'''
    Tets cases focusing on the frontend submission and update operations of students.
'''

from opensubmit.tests.cases import SubmitTestCase, rootdir

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile

class StudentSubmissionTestCase(SubmitTestCase):

    def testCanSubmitWithoutFile(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)
        # expect dashboard redirect -> 302
        # expect permission error -> 403
        cases = {
            self.openAssignment: (True, 302),
            self.softDeadlinePassedAssignment: (True, 302),
            self.hardDeadlinePassedAssignment: (False, 403),
            self.unpublishedAssignment: (False, 403),
        }
        for assignment in cases:
            response = self.c.post('/assignments/%s/new/' % assignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(submitter.user.pk)
            })
            expect_success, expected_response = cases[assignment]
            self.assertEquals(response.status_code, expected_response)

            submission_exists = Submission.objects.filter(
                assignment__exact=assignment,
                submitter__exact=submitter.user,
            ).exists()
            self.assertEquals(submission_exists, expect_success)

    def testCanSubmitWithFile(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)
        with open(rootdir+"/opensubmit/tests/submfiles/working_withsubdir.zip") as f:
            response = self.c.post('/assignments/%s/new/' % self.validatedAssignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(submitter.user.pk),
                'attachment': f
            })
        # expect dashboard redirect
        self.assertEquals(response.status_code, 302)

        sub = Submission.objects.get(
            assignment__exact=self.validatedAssignment,
            submitter__exact=submitter.user)

        assert(sub)
        assert(sub.file_upload)
        assert(sub.file_upload.md5)

    def testCannotUpdate(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)

        # pending compilation, update not allowed
        sub = self.createValidatableSubmission(self.current_user)
        response = self.c.post('/update/%u/' % sub.pk)
        self.assertEquals(response.status_code, 400)

        # test successful, update not allowed
        sub = self.createValidatedSubmission(self.current_user)
        response = self.c.post('/update/%u/' % sub.pk)
        self.assertEquals(response.status_code, 400)

    def testCanUpdateInvalidData(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)

        # Move submission into valid state for re-upload
        sub = self.createValidatableSubmission(self.current_user)
        sub.state = Submission.TEST_VALIDITY_FAILED
        sub.save()

        # Try to update file with invalid form data
        response = self.c.post('/update/%u/' % sub.pk, {'attachment':'bar'})   # invalid form data
        self.assertEquals(response.status_code, 200)    # render update view, again

    def testCanUpdateValidData(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)

        # Move submission into valid state for re-upload
        sub = self.createValidatableSubmission(self.current_user)
        sub.state = Submission.TEST_VALIDITY_FAILED
        sub.save()

        # Try to update file with correct POST data
        with open(rootdir+"/opensubmit/tests/submfiles/working_withsubdir.zip") as f:
            response = self.c.post('/update/%u/' % sub.pk, {'notes': '', 'attachment': f})
            self.assertEquals(response.status_code, 302)    # redirect to dashboard after upload

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

