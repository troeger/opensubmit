'''
    Test cases for 'GET' views and actions available for admins. They include all cases for teachers through inheritance.
'''

from opensubmit.models import SubmissionFile
from django.contrib.auth.models import User
from django.core.files import File

from opensubmit.tests.cases import SubmitAdminTestCase
from opensubmit.tests.test_teacher import TeacherTestCaseSet

class AdminTestCase(SubmitAdminTestCase, TeacherTestCaseSet):
    def testMergeUsersView(self):
        response=self.c.get('/mergeusers/?primary_id=%u&secondary_id=%u'%
            (self.enrolled_students[0].user.pk, self.enrolled_students[1].user.pk))
        self.assertEquals(response.status_code, 200)

    def testMergeUsersAction(self):
        response=self.c.post('/mergeusers/', {
            'primary_id':self.enrolled_students[0].user.pk,
            'secondary_id':self.enrolled_students[1].user.pk})
        self.assertEquals(response.status_code, 302)

    def testTestMachineListView(self):
        # one machine given
        self.createTestMachine('127.0.0.1')
        response=self.c.get('/admin/opensubmit/testmachine/')
        self.assertEquals(response.status_code, 200)

    def testCanUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 200)

