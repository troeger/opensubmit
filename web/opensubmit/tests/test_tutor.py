'''
    Test cases for tutor 'GET' views and actions.
'''

from opensubmit.models import Assignment, Submission
from opensubmit.tests.cases import SubmitTutorTestCase

from .helpers.user import get_student_dict, create_user, admin_dict
from .helpers.submission import create_validated_submission
from .helpers.submission import create_validatable_submission
from .helpers.djangofiles import create_submission_file
from .helpers.course import create_course
from .helpers.assignment import create_pass_fail_grading
from .helpers.assignment import create_open_file_assignment

from django.contrib.admin.sites import AdminSite


class Tutor(SubmitTutorTestCase):

    def setUp(self):
        super(Tutor, self).setUp()
        self.admin = create_user(admin_dict)
        self.course = create_course(self.admin, self.user)
        grading = create_pass_fail_grading()
        self.assignment = create_open_file_assignment(self.course, grading)

    def test_teacher_dashboard_view(self):
        response = self.c.get('/teacher/')
        self.assertEqual(response.status_code, 200)

    def test_assignment_list_backend(self):
        from opensubmit.admin.assignment import AssignmentAdmin
        assadm = AssignmentAdmin(Assignment, AdminSite())
        assignments_shown = assadm.get_queryset(self.request)
        self.assertIn(self.assignment, assignments_shown)

    def test_submission_list_view(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEqual(response.status_code, 200)

    def test_submission_edit_view(self):
        sub = create_validated_submission(self.user, self.assignment)
        response = self.c.get(
            '/teacher/opensubmit/submission/%u/change/' % sub.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(sub.get_validation_result().result))

    def test_grading_table_view(self):
        response = self.c.get('/course/%u/gradingtable/' % self.course.pk)
        self.assertEqual(response.status_code, 200)

    def test_duplicate_report_view(self):
        sub1 = create_validatable_submission(
            create_user(get_student_dict(0)),
            self.assignment,
            create_submission_file())
        sub2 = create_validatable_submission(
            create_user(get_student_dict(1)),
            self.assignment,
            create_submission_file())
        sub3 = create_validatable_submission(
            create_user(get_student_dict(2)),
            self.assignment,
            create_submission_file())
        sub3.state = Submission.WITHDRAWN
        sub3.save()
        response = self.c.get('/assignments/%u/duplicates/' %
                              self.assignment.pk)
        self.assertEqual(response.status_code, 200)
        # expect both submissions to be in the report
        self.assertIn('submission/%u/change' % sub1.pk, str(response.content))
        self.assertIn('submission/%u/change' % sub2.pk, str(response.content))
        # expect withdrawn submissions to be left out
        self.assertNotIn('#%u' % sub3.pk, str(response))

    def test_preview_view(self):
        sub1 = create_validated_submission(self.user, self.assignment)
        response = self.c.get('/preview/%u/' % sub1.pk)
        self.assertEqual(response.status_code, 200)

    def test_preview_broken_view(self):
        '''
            Test proper handling of archives containing
            files with invalid unicode.
        '''
        sub1 = create_validated_submission(self.user, self.assignment)
        for fname in ['broken_preview.gz',
                      'broken_preview2.gz',
                      'broken_preview.zip']:
            subfile = create_submission_file(
                "submfiles/broken_preview/" + fname)
            sub1.file_upload = subfile
            sub1.save()
            response = self.c.get('/preview/%u/' % sub1.pk)
            self.assertEqual(response.status_code, 200)

    def test_add_course_tutor_signal_handler(self):
        # Add another user who had no backend rights before
        new_user = create_user(get_student_dict(1))
        new_user.save()
        assert(not new_user.is_staff)
        self.course.tutors.add(new_user)
        self.course.save()
        # Check if he got them afterwards
        new_user.refresh_from_db()
        assert(new_user.is_staff)

    def test_remove_course_tutor_signal_handler(self):
        assert(self.user in self.course.tutors.all())
        assert(self.user.is_staff)
        self.course.tutors.remove(self.user)
        self.course.save()
        self.user.refresh_from_db()
        assert(not self.user.is_staff)

