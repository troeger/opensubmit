'''
    Test cases focusing on the model admin extensions.
'''

from .helpers.assignment import *
from .helpers.submission import *
from .helpers.course import create_course
from .helpers.user import create_user, admin_dict
from .cases import SubmitTutorTestCase
from django.test.utils import override_settings


from opensubmit.admin.course import CourseAdmin
from opensubmit.models import Assignment, Course
from opensubmit.models import SubmissionFile, Submission
from opensubmit.models import GradingScheme

from django.contrib.admin.sites import AdminSite


class ModelAdminTestCase(SubmitTutorTestCase):

    def test_submission_file_backend(self):
        from opensubmit.admin.submissionfile import SubmissionFileAdmin
        subfileadm = SubmissionFileAdmin(SubmissionFile, AdminSite())
        files_shown = subfileadm.get_queryset(self.request).count()
        self.assertEqual(0, files_shown)

    def test_grading_scheme_admin_rendering(self):
        from opensubmit.admin.gradingscheme import GradingSchemeAdmin
        gsadmin = GradingSchemeAdmin(GradingScheme, AdminSite())
        assert('GradingSchemeForm' in str(gsadmin.get_form(self.request)))


class SubmissionModelAdminTestCase(SubmitTutorTestCase):
    '''
        Test submission model admin functions, which needs more setUp
        than the other cases.
    '''

    def setUp(self):
        from opensubmit.admin.submission import SubmissionAdmin
        super(SubmissionModelAdminTestCase, self).setUp()
        # Tutor is already logged in, we need an additional admin
        self.admin = create_user(admin_dict)
        # Prepare assignments
        self.course = create_course(self.admin, self.user)
        self.grading_scheme = create_pass_fail_grading()
        self.assign1 = create_open_assignment(
            self.course, self.grading_scheme)
        self.assign2 = create_soft_passed_assignment(
            self.course, self.grading_scheme)
        self.assign3 = create_validated_assignment_with_archive(
            self.course, self.grading_scheme)
        self.all_assignments = [self.assign1, self.assign2, self.assign3]
        # Prepare submissions
        self.sub1 = create_submission(self.user, self.assign1)
        self.sub2 = create_submission(self.user, self.assign2)
        self.sub3 = create_validated_submission(self.user, self.assign3)
        self.all_submissions = [self.sub1, self.sub2, self.sub3]

        self.submadm = SubmissionAdmin(Submission, AdminSite())

    def test_submission_backend(self):
        submissions = self.submadm.get_queryset(self.request)
        for sub in submissions:
            self.assertIn(sub, self.all_submissions)
        self.assertEqual(len(submissions), len(self.all_submissions))

    def test_course_backend(self):
        from opensubmit.admin.course import assignments as course_assignments
        courseadm = CourseAdmin(Course, AdminSite())
        num_courses = courseadm.get_queryset(self.request).count()
        self.assertEqual(num_courses, 1)
        ass_str_list = course_assignments(self.course)
        for ass in self.all_assignments:
            assert(ass.title in ass_str_list)

    def test_assignment_backend(self):
        from opensubmit.admin.assignment import AssignmentAdmin
        assadm = AssignmentAdmin(Assignment, AdminSite())
        assignments_shown = assadm.get_queryset(self.request).count()
        # should get all of them
        self.assertEqual(len(self.all_assignments), assignments_shown)

    def test_course_list_from_grading_scheme(self):
        from opensubmit.admin.gradingscheme import courses
        course_list = courses(self.grading_scheme)
        assert(self.course.title in course_list)

    def test_close_and_notify(self):
        from django.core import mail
        # Everything in status 'SUBMITTED', so no mail should be sent
        self.submadm.closeAndNotifyAction(
            self.request, Submission.objects.all())
        self.assertEqual(0, len(mail.outbox))
        # One mail should be sent
        self.sub1.state = Submission.GRADED
        self.sub1.save()
        self.sub2.state = Submission.GRADED
        self.sub2.save()
        self.submadm.closeAndNotifyAction(
            self.request, Submission.objects.all())
        self.assertEqual(2, len(mail.outbox))
        for email in mail.outbox:
            self.assertIn("Grading", email.subject)
            self.assertIn("grading", email.body)
            self.assertIn("localhost", email.body)

    @override_settings(MAIN_URL='http://localhost:8001/foobar')
    @override_settings(HOST='localhost:8001')
    @override_settings(HOST_DIR='/foobar')
    @override_settings(FORCE_SCRIPT_NAME='/foobar')
    def test_email_link(self):
        from django.core import mail
        # One mail should be sent
        self.sub1.state = Submission.GRADED
        self.sub1.save()
        self.submadm.closeAndNotifyAction(
            self.request, Submission.objects.all())
        for email in mail.outbox:
            self.assertIn("Grading", email.subject)
            self.assertIn("grading", email.body)
            self.assertIn("http://localhost:8001/foobar/details", email.body)

    def test_set_full_pending_all(self):
        # Only one of the submission assignments has validation configured
        self.submadm.setFullPendingStateAction(
            self.request, Submission.objects.all())
        self.assertEqual(1, Submission.objects.filter(
            state=Submission.TEST_FULL_PENDING).count())

    def test_set_full_pending_none_matching(self):
        # Only one of the submission assignments has validation configured
        self.submadm.setFullPendingStateAction(
            self.request, Submission.objects.filter(
                state=Submission.SUBMITTED))
        self.assertEqual(0, Submission.objects.filter(
            state=Submission.TEST_FULL_PENDING).count())

    def test_set_initial_state(self):
        self.submadm.setInitialStateAction(
            self.request, Submission.objects.all())
        self.assertEqual(2, Submission.objects.filter(
            state=Submission.SUBMITTED).count())

    def test_grading_file_indicator(self):
        from django.core.files import File as DjangoFile
        from opensubmit.admin.submission import grading_file
        self.assertEqual(False, grading_file(self.sub1))
        self.sub1.grading_file = DjangoFile(
            open(__file__), str("grading_file.txt"))
        self.sub1.save()
        self.assertEqual(True, grading_file(self.sub1))

    def test_state_filter(self):
        from opensubmit.admin.submission import SubmissionStateFilter
        submfilter = SubmissionStateFilter(
            self.request, {'statefilter': 'tobegraded'}, Submission, None)
        for sub in submfilter.queryset(self.request, Submission.objects.all()):
            assert(sub in self.all_submissions)
        graded_count = SubmissionStateFilter(
            self.request, {'statefilter': 'graded'},
            Submission,
            None).queryset(
            self.request, Submission.objects.all()).count()
        self.assertEqual(graded_count, 0)

    def test_assignment_filter(self):
        from opensubmit.admin.submission import SubmissionAssignmentFilter
        submfilter = SubmissionAssignmentFilter(
            self.request, {'assignmentfilter': self.sub1.assignment.pk},
            Submission, None)
        sublist = submfilter.queryset(
            self.request, Submission.objects.all()).values_list(
            'pk', flat=True)
        self.assertSequenceEqual(sublist, [self.sub1.pk])

    def test_course_filter(self):
        from opensubmit.admin.submission import SubmissionCourseFilter
        submfilter = SubmissionCourseFilter(
            self.request, {'coursefilter': self.course.pk}, Submission, None)
        subcount = submfilter.queryset(
            self.request, Submission.objects.all()).count()
        self.assertEqual(subcount, len(self.all_submissions))
