'''
    Test cases focusing on the frontend submission and
    update operations of students.
'''

from opensubmit.models import Submission
from opensubmit.tests.cases import SubmitStudentScenarioTestCase
from opensubmit.tests import rootdir
from .helpers.submission import create_validatable_submission
from .helpers.user import create_user, get_student_dict


class Student(SubmitStudentScenarioTestCase):

    def test_can_submit_without_file(self):
        # expect dashboard redirect -> 302
        # expect permission error -> 403
        cases = {
            self.open_assignment: (True, 302),
            self.soft_deadline_passed_assignment: (True, 302),
            self.hard_deadline_passed_assignment: (False, 403),
            self.unpublished_assignment: (False, 403),
        }
        for assignment in cases:
            response = self.c.post('/assignments/%s/new/' % assignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(self.user.pk)
            })
            expect_success, expected_response = cases[assignment]
            self.assertEqual(response.status_code, expected_response)

            submission_exists = Submission.objects.filter(
                assignment__exact=assignment,
                submitter__exact=self.user,
            ).exists()
            self.assertEqual(submission_exists, expect_success)

    def test_can_submit_with_file(self):
        with open(rootdir + "submfiles/1000tff/packed.zip", 'rb') as f:
            response = self.c.post('/assignments/%s/new/' % self.validated_assignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(self.user.pk),
                'attachment': f
            })
        # expect dashboard redirect
        self.assertEqual(response.status_code, 302)

        sub = Submission.objects.get(
            assignment__exact=self.validated_assignment,
            submitter__exact=self.user)

        assert(sub)
        assert(sub.file_upload)
        assert(sub.file_upload.md5)

    def test_md5_on_submit_generation(self):
        def submit(submitter, filename):
            self.loginUser(submitter)
            with open(rootdir + "/opensubmit/tests/submfiles/" + filename, 'rb') as f:
                response = self.c.post('/assignments/%s/new/' % self.fileAssignment.pk, {
                    'notes': 'This is a test submission.',
                    'authors': str(submitter.user.pk),
                    'attachment': f
                })
                return Submission.objects.get(
                    assignment__exact=self.file_assignment,
                    submitter__exact=submitter.user)
        md5_1 = submit(self.user, 'django.pdf').file_upload.md5
        md5_2 = submit(self.another_user, 'python.pdf').file_upload.md5
        self.assertNotEqual(md5_1, md5_2)

    def test_cannot_update(self):
        # pending compilation, update not allowed
        sub = create_validatable_submission(self.user)
        response = self.c.post('/update/%u/' % sub.pk)
        # expect dashboard redirect
        self.assertEqual(response.status_code, 302)

        # test successful, update not allowed
        sub = create_validated_submission(self.user)
        response = self.c.post('/update/%u/' % sub.pk)
        # expect dashboard redirect
        self.assertEqual(response.status_code, 302)

    def test_can_update_invalid_data(self):
        # Move submission into valid state for re-upload
        sub = create_validatable_submission(self.user)
        sub.state = Submission.TEST_VALIDITY_FAILED
        sub.save()

        # Try to update file with invalid form data
        response = self.c.post('/update/%u/' % sub.pk,
                               {'attachment': 'bar'})   # invalid form data
        # render update view, again
        self.assertEqual(response.status_code, 200)

    def test_can_update_valid_data(self):
        # Move submission into valid state for re-upload
        sub = create_validatable_submission(self.user)
        sub.state = Submission.TEST_VALIDITY_FAILED
        sub.save()

        # Try to update file with correct POST data
        with open(rootdir + "/opensubmit/tests/submfiles/1000tff/packed.zip", 'rb') as f:
            response = self.c.post('/update/%u/' % sub.pk,
                                   {'notes': '', 'attachment': f})
            # redirect to dashboard after upload
            self.assertEqual(response.status_code, 302)

    def test_non_enrolled_cannot_submit(self):
        submitter = self.not_enrolled_students[0]
        self.loginUser(submitter)
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This submission will fail because the user
                        is not enrolled in the course that the
                        assignment belongs to""",
            'authors': str(submitter.user.pk)
        })
        self.assertEqual(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=submitter.user,
            assignment__exact=self.openAssignment,
        ).count()
        self.assertEqual(submission_count, 0)

    def test_can_submit_as_team(self):
        second_guy = create_user(get_student_dict(1))
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(second_guy.pk),
        })
        self.assertIn(response.status_code, (200, 302, ))

        submission = Submission.objects.get(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.openAssignment,
        )
        self.assertTrue(submission.authors.filter(
            pk__exact=self.enrolled_students[1].user.pk).exists())

    def test_cannot_submit_as_team_without_enrollment(self):
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.not_enrolled_students[0].user.pk),
        })
        self.assertEqual(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.open_assignment,
        ).count()
        self.assertEqual(submission_count, 0)

    def test_cannot_double_submit_through_team(self):
        self.create_and_login_user(get_student_dict(1))
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This is a solution that student1 has submitted.""",
            'authors': str(submitter.user.pk)
        })
        self.assertIn(response.status_code, (302, 200, ))

        first_submission_exists = Submission.objects.filter(
            submitter__exact=submitter.user,
            assignment__exact=self.open_assignment,
        ).exists()
        self.assertTrue(first_submission_exists)

        self.loginUser(self.enrolled_students[0])
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.enrolled_students[1].user.pk),
        })
        self.assertEqual(response.status_code, 403)

        submission_exists = Submission.objects.filter(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.open_assignment,
        ).exists()
        self.assertFalse(submission_exists)
