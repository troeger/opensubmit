from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import LiveServerTestCase, TestCase
from django.test.utils import override_settings
from django.test import client
from django.apps import apps
from django import db, http

from opensubmit.tests.helpers.user import *


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
        self.create_and_login_user(enrolled_students_dict[0])
        self.request = MockRequest(self.user)


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
