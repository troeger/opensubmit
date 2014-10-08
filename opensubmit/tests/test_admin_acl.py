from opensubmit.tests.cases import *

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile


class AdminACLTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(AdminACLTestCase, self).setUp()

    def testCanUseTeacherBackend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 200)        

    def testCanUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 200)        
