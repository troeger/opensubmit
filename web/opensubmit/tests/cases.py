from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import LiveServerTestCase, TestCase
from django.test.utils import override_settings
from django.test import client
from django.apps import apps
from django import db, http

from .helpers.user import *
from .helpers.assignment import *
from .helpers.course import create_course
from .helpers.submission import create_submission


class MockRequest(http.HttpRequest):
    def __init__(self, user):
        self.user = user
        # Needed for mocking a functioning messaging middleware
        # see https://code.djangoproject.com/ticket/17971
        self.session = 'session'
        self._messages = FallbackStorage(self)


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher', ])
@override_settings(MEDIA_ROOT='/tmp/')
class SubmitTestCase(LiveServerTestCase):
    def create_and_login_user(self, user_struct):
        self.user_struct = user_struct
        self.user = create_user(user_struct)
        self.c = client.Client()
        self.c.login(username=user_struct['username'],
                     password=user_struct['password'])


class SubmitAdminTestCase(SubmitTestCase):
    '''
    Test case with an admin logged-in.
    '''

    def setUp(self):
        super(SubmitAdminTestCase, self).setUp()
        self.create_and_login_user(admin_dict)
        self.request = MockRequest(self.user)
        # Test for amok-running post_save handlers (we had such a case)
        assert(self.user.is_active)
        assert(self.user.is_superuser)
        assert(self.user.is_staff)


class SubmitTeacherTestCase(SubmitTestCase):
    '''
    Test case with an teacher (course owner) logged-in.
    '''

    def setUp(self):
        super(SubmitTeacherTestCase, self).setUp()
        self.create_and_login_user(teacher_dict)
        self.request = MockRequest(self.user)
        # Test for amok-running post_save handlers (we had such a case)
        assert(self.user.is_active)
        assert(self.user.is_staff)


class SubmitTutorTestCase(SubmitTestCase):
    '''
    Test case with a tutor logged-in.
    '''

    def setUp(self):
        super(SubmitTutorTestCase, self).setUp()
        self.create_and_login_user(tutor_dict)
        self.request = MockRequest(self.user)
        # Test for amok-running post_save handlers (we had such a case)
        assert(self.user.is_active)
        assert(not self.user.is_superuser)
        assert(self.user.is_staff)


class SubmitStudentTestCase(SubmitTestCase):
    '''
    Test case with a student logged-in.
    '''

    def setUp(self):
        super(SubmitStudentTestCase, self).setUp()
        self.create_and_login_user(get_student_dict(0))
        self.request = MockRequest(self.user)


class SubmitStudentScenarioTestCase(SubmitStudentTestCase):
    '''
    As above, but with a common set of prepared resources
    from a default usage scenario.

    To speed up test runs, it is preferrable to create
    the needed resources explicitely, instead of inherting
    from this class.
    '''
    def setUp(self):
        super(SubmitStudentScenarioTestCase, self).setUp()
        self.admin = create_user(admin_dict)
        self.teacher = create_user(teacher_dict)
        self.tutor = create_user(tutor_dict)
        self.course = create_course(self.admin)
        self.another_course = create_course(self.admin)
        grading = create_pass_fail_grading()

        self.open_assignment = create_open_assignment(
            self.course, grading)
        self.soft_deadline_passed_assignment = create_soft_passed_assignment(
            self.course, grading)
        self.hard_deadline_passed_assignment = create_hard_passed_assignment(
            self.course, grading)
        self.no_hard_assignment = create_no_hard_soft_passed_assignment(
            self.course, grading)
        self.no_grading_assignment = create_no_grading_assignment(
            self.course)
        self.unpublished_assignment = create_unpublished_assignment(
            self.course, grading)
        self.uploaded_desc_assignment = create_uploaded_desc_assignment(
            self.course, grading)

        self.all_assignments = (
            self.open_assignment,
            self.soft_deadline_passed_assignment,
            self.hard_deadline_passed_assignment,
            self.no_hard_assignment,
            self.no_grading_assignment,
            self.unpublished_assignment,
            self.uploaded_desc_assignment
        )

        self.open_assignment_sub = create_submission(
            self.user,
            self.open_assignment)
        self.soft_deadline_passed_assignment_sub = create_submission(
            self.user,
            self.soft_deadline_passed_assignment)
        self.hard_deadline_passed_assignment_sub = create_submission(
            self.user,
            self.hard_deadline_passed_assignment)
        self.no_hard_assignment_sub = create_submission(
            self.user,
            self.no_hard_assignment)
        self.no_grading_assignment_sub = create_submission(
            self.user,
            self.no_grading_assignment)
        self.unpublished_assignment_sub = create_submission(
            self.user,
            self.unpublished_assignment)
        self.uploaded_desc_assignment_sub = create_submission(
            self.user,
            self.uploaded_desc_assignment)

        self.submissions = (
            self.open_assignment_sub,
            self.soft_deadline_passed_assignment_sub,
            self.hard_deadline_passed_assignment_sub,
            self.no_hard_assignment_sub,
            self.no_grading_assignment_sub,
            self.unpublished_assignment_sub,
            self.uploaded_desc_assignment_sub
        )


class TestMigrations(TestCase):
    '''
    Taken from https://www.caktusgroup.com/blog/2016/02/02/
    '''

    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    migrate_from = None
    migrate_to = None

    def setUp(self):
        assert self.migrate_from and self.migrate_to
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = db.migrations.executor.MigrationExecutor(db.connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = db.migrations.executor.MigrationExecutor(db.connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass
