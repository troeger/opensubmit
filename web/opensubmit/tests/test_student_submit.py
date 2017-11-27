'''
    Test cases focusing on the frontend submission and
    update operations of students.
'''

from opensubmit.models import Submission
from opensubmit.tests.cases import SubmitStudentScenarioTestCase
from opensubmit.tests import rootdir
from .helpers.submission import create_validatable_submission
from .helpers.submission import create_validated_submission
from .helpers.user import get_student_dict, create_user
from .helpers.djangofiles import create_submission_file


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
        with open(rootdir + "submfiles/validation/1000tff/packed.zip", 'rb') as f:
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
        with open(rootdir + 'submfiles/validation/0100fff/python.pdf', 'rb') as f:
            response = self.c.post('/assignments/%s/new/' % self.open_file_assignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(self.user.pk),
                'attachment': f
            })
            self.assertEqual(302, response.status_code)
        sub = Submission.objects.get(
            assignment=self.open_file_assignment,
            submitter=self.user)
        md5_1 = sub.file_upload.md5

        self.create_and_login_user(get_student_dict(1))
        self.course.participants.add(self.user.profile)

        with open(rootdir + 'submfiles/duplicates/duplicate_orig.zip', 'rb') as f:
            response = self.c.post('/assignments/%s/new/' % self.open_file_assignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(self.user.pk),
                'attachment': f
            })
            self.assertEqual(302, response.status_code)
        sub = Submission.objects.get(
            assignment__exact=self.open_file_assignment,
            submitter__exact=self.user)
        md5_2 = sub.file_upload.md5

        self.assertNotEqual(md5_1, md5_2)

    def test_cannot_update(self):
        # pending compilation, update not allowed
        f = create_submission_file()
        sub = create_validatable_submission(
            self.user, self.open_file_assignment, f)
        response = self.c.post('/update/%u/' % sub.pk)
        # expect dashboard redirect
        self.assertEqual(response.status_code, 302)

        # test successful, update not allowed
        sub = create_validated_submission(self.user, self.open_file_assignment)
        response = self.c.post('/update/%u/' % sub.pk)
        # expect dashboard redirect
        self.assertEqual(response.status_code, 302)

    def test_can_update_invalid_data(self):
        # Move submission into valid state for re-upload
        f = create_submission_file()
        sub = create_validatable_submission(
            self.user, self.open_file_assignment, f)
        sub.state = Submission.TEST_VALIDITY_FAILED
        sub.save()

        # Try to update file with invalid form data
        response = self.c.post('/update/%u/' % sub.pk,
                               {'attachment': 'bar'})   # invalid form data
        # render update view, again
        self.assertEqual(response.status_code, 200)

    def test_can_update_valid_data(self):
        # Move submission into valid state for re-upload
        f = create_submission_file()
        sub = create_validatable_submission(
            self.user, self.open_file_assignment, f)
        sub.state = Submission.TEST_VALIDITY_FAILED
        sub.save()

        # Try to update file with correct POST data
        with open(rootdir + "submfiles/validation/1000tff/packed.zip", 'rb') as f:
            response = self.c.post('/update/%u/' % sub.pk,
                                   {'notes': '', 'attachment': f})
            # redirect to dashboard after upload
            self.assertEqual(response.status_code, 302)

    def test_non_enrolled_cannot_submit(self):
        self.create_and_login_user(get_student_dict(1))
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This submission will fail because the user
                        is not enrolled in the course that the
                        assignment belongs to""",
            'authors': str(self.user.pk)
        })
        self.assertEqual(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=self.user,
            assignment__exact=self.open_assignment,
        ).count()
        self.assertEqual(submission_count, 0)

    def test_can_submit_as_team(self):
        second_guy = create_user(get_student_dict(1))

        # Try to use second_guy as co-author, without him
        # being part of the course
        # The UI should prevent that anyway
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(second_guy.pk),
        })
        self.assertEqual(403, response.status_code)

        # Add second guy to course, should work now
        self.course.participants.add(second_guy.profile)
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(second_guy.pk),
        })
        self.assertEqual(302, response.status_code)

        # Submission should now be there with correct list of authors
        submission = Submission.objects.get(
            submitter__exact=self.user,
            assignment__exact=self.open_assignment,
        )
        self.assertTrue(submission.authors.filter(
            pk__exact=second_guy.pk).exists())

    def test_cannot_submit_as_team_without_enrollment(self):
        not_enrolled = create_user(get_student_dict(1))
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(not_enrolled.pk),
        })
        self.assertEqual(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=self.user,
            assignment__exact=self.open_assignment,
        ).count()
        self.assertEqual(submission_count, 0)

    def test_cannot_double_submit_through_team(self):
        first_guy = self.user
        second_guy = create_user(get_student_dict(1))
        self.course.participants.add(second_guy.profile)
        self.course.save()

        response = self.c.post('/assignments/%s/new/' %
                               self.open_assignment.pk, {
                                   'notes': "This is a solution that student0 has submitted.",
                                   'authors': str(second_guy.pk)
                               })
        self.assertIn(response.status_code, (302, 200, ))

        first_submission_exists = Submission.objects.filter(
            submitter__exact=self.user,
            assignment__exact=self.open_assignment,
        ).exists()
        self.assertTrue(first_submission_exists)

        self.login_user(get_student_dict(1))
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This submission is handed in by student1,
                        who collaborated with student0 on the
                        assignment.""",
            'authors': str(first_guy.pk),
        })
        self.assertEqual(response.status_code, 403)
        response = self.c.post('/assignments/%s/new/' % self.open_assignment.pk, {
            'notes': """This assignment is handed in by student1 alone.""",
        })
        self.assertEqual(response.status_code, 403)

        submission_exists = Submission.objects.filter(
            submitter__exact=second_guy,
            assignment__exact=self.open_assignment,
        ).exists()
        self.assertFalse(submission_exists)
