from opensubmit.tests.cases import *

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile


class TutorACLTestCase(SubmitTutorTestCase):
    def setUp(self):
        super(TutorACLTestCase, self).setUp()

    def testCannUseTeacherBackend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 200)        # Redirect to login page

    def testCannotUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 302)        # Redirect to login page
