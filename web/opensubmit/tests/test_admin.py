'''
    Test cases for 'GET' views and actions available for admins. They include all cases for teachers through inheritance.
'''

from django.contrib.auth.models import User
from django.core.files import File

from opensubmit.models import SubmissionFile
from .cases import SubmitAdminTestCase
from .test_teacher import TeacherTestCase

class AdminTestCase(SubmitAdminTestCase, TeacherTestCase):
    def testMergeUsersView(self):
        response=self.c.get('/mergeusers/?primary_id=%u&secondary_id=%u'%
            (self.enrolled_students[0].user.pk, self.enrolled_students[1].user.pk))
        self.assertEqual(response.status_code, 200)

    def testMergeUsersAction(self):
        response=self.c.post('/mergeusers/', {
            'primary_id':self.enrolled_students[0].user.pk,
            'secondary_id':self.enrolled_students[1].user.pk})
        self.assertEqual(response.status_code, 302)

    def testTestMachineListView(self):
        # one machine given
        self.createTestMachine('127.0.0.1')
        response=self.c.get('/teacher/opensubmit/testmachine/')
        self.assertEqual(response.status_code, 200)

    def testCanUseAdminBackend(self):
        response = self.c.get('/teacher/auth/user/')
        self.assertEqual(response.status_code, 200)

