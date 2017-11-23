'''
    Test cases for teacher 'GET' views and actions.
    They include all cases for tutors by inheritance.
'''

import io
import zipfile

from django.contrib.auth.models import User

from opensubmit.models import Submission
from .cases import SubmitTeacherTestCase
from .helpers.course import create_course
from .helpers.submission import create_validated_submission
from .helpers.submission import create_validatable_submission
from .helpers.assignment import create_pass_fail_grading
from .helpers.assignment import create_all_assignments
from .helpers.assignment import create_open_file_assignment
from .helpers.assignment import get_pass_grading
from .helpers.djangofiles import create_submission_file
from .helpers.user import create_user, get_student_dict


class Teacher(SubmitTeacherTestCase):
    def setUp(self):
        super(Teacher, self).setUp()

        # Prepare assignments
        self.course = create_course(self.user)
        self.student = create_user(get_student_dict(1))
        self.course.participants.add(self.student.profile)
        self.course.save()
        self.grading_scheme = create_pass_fail_grading()
        self.all_assignments = create_all_assignments(
            self.course, self.grading_scheme)
        self.assignment = create_open_file_assignment(
            self.course, self.grading_scheme)

    def test_new_assignment_view(self):
        response = self.c.get('/teacher/opensubmit/assignment/add/')
        self.assertEqual(response.status_code, 200)

    def test_edit_assignment_view(self):
        for ass in self.all_assignments:
            response = self.c.get(
                '/teacher/opensubmit/assignment/%u/change/' % ass.pk)
            self.assertEqual(response.status_code, 200)

    def test_grading_scheme_list_view(self):
        response = self.c.get('/teacher/opensubmit/gradingscheme/')
        self.assertEqual(response.status_code, 200)

    def test_grading_list_view(self):
        response = self.c.get('/teacher/opensubmit/grading/')
        self.assertEqual(response.status_code, 200)

    def test_assignment_list_view(self):
        response = self.c.get('/teacher/opensubmit/assignment/')
        self.assertEqual(response.status_code, 200)

    def test_course_list_view(self):
        response = self.c.get('/teacher/opensubmit/course/')
        self.assertEqual(response.status_code, 200)

    def test_grading_table_view(self):
        sub = create_validated_submission(self.user, self.assignment)
        sub.grading = get_pass_grading(self.grading_scheme)
        sub.state = Submission.CLOSED
        sub.save()
        response = self.c.get('/course/%u/gradingtable/' % self.course.pk)
        self.assertEqual(response.status_code, 200)

    def test_submission_file_list_view(self):
        response = self.c.get('/teacher/opensubmit/submissionfile/')
        self.assertEqual(response.status_code, 200)

    def test_mail_view(self):
        response = self.c.get('/course/%u/mail2all/' % self.course.pk)
        self.assertEqual(response.status_code, 200)

    def test_mail_sending(self):
        # POST with parameters leads to preview, which stores relevant information in session
        response = self.c.post('/course/%u/mail2all/' %
                               self.course.pk, {'subject': 'Foo', 'message': 'bar'})
        self.assertEqual(response.status_code, 200)
        # POST without parameters leads to sending of data stored in session
        # Expect redirect to overview
        response = self.c.post('/course/%u/mail2all/' % self.course.pk)
        self.assertEqual(response.status_code, 302)

    def test_perf_data_view(self):
        sub1 = create_validated_submission(self.user, self.assignment)
        sub2 = create_validated_submission(self.user, self.assignment)
        response = self.c.get('/assignments/%u/perftable/' %
                              sub1.assignment.pk)
        # Resulting CSV should have header line + 2 result lines + empty final line
        csv = response.content.decode(response.charset)
        self.assertEqual(response.status_code, 200)
        # content type
        self.assertIn('text/csv', response['Content-Type'])
        self.assertEqual(len(csv.split('\n')), 3 + 1)

    def test_course_archive_view(self):
        # add some student upload to be stored in the archive
        create_validated_submission(self.user, self.assignment)
        response = self.c.get('/course/%u/archive/' % self.course.pk)
        self.assertEqual(response.status_code, 200)
        # Test if the download is really a ZIP file
        f = io.BytesIO(response.content)
        zipped_file = zipfile.ZipFile(f, 'r')
        try:
            # Check ZIP file validity
            self.assertIsNone(zipped_file.testzip())
            # Try to find a file some student stored in a
            # sub-folder on it's own, targets #18
            found_stud_subfile = False
            for entry in zipped_file.filelist:
                if "subdir" in entry.filename:
                    found_stud_subfile = True
            assert(found_stud_subfile)
        finally:
            zipped_file.close()
            f.close()

    def test_course_archive_with_non_zip_view(self):
        # add some student upload to be stored in the archive
        non_zip = create_submission_file(
            relpath="/submfiles/validation/1000fff/helloworld.c")
        create_validatable_submission(
            self.user, self.assignment, non_zip)
        response = self.c.get('/course/%u/archive/' % self.course.pk)
        self.assertEqual(response.status_code, 200)

    def test_assignment_archive_view(self):
        # add some student upload to be stored in the archive
        zip_file = create_submission_file(
            relpath="/submfiles/validation/1000tff/packed.zip")
        create_validatable_submission(
            self.user, self.assignment, zip_file)
        response = self.c.get('/assignments/%u/archive/' %
                              self.assignment.pk)
        self.assertEqual(response.status_code, 200)
        # Test if the download is really a ZIP file
        f = io.BytesIO(response.content)
        zipped_file = zipfile.ZipFile(f, 'r')
        try:
            # Check ZIP file validity
            self.assertIsNone(zipped_file.testzip())
        finally:
            zipped_file.close()
            f.close()

    def test_assignment_archive_with_non_zip_view(self):
        # add some student upload to be stored in the archive
        non_zip = create_submission_file(
            relpath="/submfiles/validation/1000fff/helloworld.c")
        create_validatable_submission(
            self.user, self.assignment, non_zip)
        response = self.c.get('/assignments/%u/archive/' %
                              self.assignment.pk)
        self.assertEqual(response.status_code, 200)

    def test_change_course_owner_signal_handler(self):
        # Get a course with some owner
        # Assign new owner who had no backend rights before
        new_owner = User(username='foo')
        new_owner.save()
        assert(not new_owner.is_staff)
        old_owner_name = self.course.owner.username
        self.course.owner = new_owner
        self.course.save()
        # Make sure the old one has no more rights
        old_owner = User.objects.get(username=old_owner_name)
        assert(not old_owner.is_staff)
        # Make sure the new one has now backend rights
        new_owner = User.objects.get(username='foo')
        assert(new_owner.is_staff)
