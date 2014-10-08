from opensubmit.tests.cases import *

class TutorACLTestCase(SubmitTutorTestCase):
    def setUp(self):
        super(TutorACLTestCase, self).setUp()

    def testCannUseTeacherBackend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 200)        

    def testCannotUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 403)        # Raise permission denied

