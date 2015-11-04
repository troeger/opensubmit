'''
    Test cases for views, both in student frontend and teacher backend.
'''

from opensubmit.tests.cases import StudentTestCase, SubmitAdminTestCase
from django.contrib.auth.models import User

class StudentViewsTestCase(StudentTestCase):
    def setUp(self):
        super(StudentViewsTestCase, self).setUp()
        self.val_sub = self.createValidatedSubmission(self.current_user)

    def testIndexView(self):
        # User is already logged in, expecting dashboard redirect
        response=self.c.get('/')
        self.assertEquals(response.status_code, 302)

    def testLogoutView(self):
        # User is already logged in, expecting redirect
        response=self.c.get('/logout/')
        self.assertEquals(response.status_code, 302)

    def testSettingsView(self):
        response=self.c.get('/settings/')
        self.assertEquals(response.status_code, 200)
        # Send new data, saving should redirect to dashboard
        response=self.c.post('/settings/',
            {'username':'foobar',
             'first_name': 'Foo',
             'last_name': 'Bar',
             'email': 'foo@bar.eu'}
        )
        self.assertEquals(response.status_code, 302)
        u = User.objects.get(pk=self.current_user.user.pk)
        self.assertEquals(u.username, 'foobar')

    def testCoursesView(self):
        response=self.c.get('/courses/')
        self.assertEquals(response.status_code, 200)

    def testEnforcedUserSettingsView(self):
        self.current_user.user.first_name=""
        self.current_user.user.save()
        response=self.c.get('/dashboard/')
        self.assertEquals(response.status_code, 302)

    def testDashboardView(self):
        response=self.c.get('/dashboard/')
        self.assertEquals(response.status_code, 200)

    def testMachineView(self):
        response=self.c.get('/machine/%u/'%self.machine.pk)
        self.assertEquals(response.status_code, 200)

class AdminViewsTestCase(SubmitAdminTestCase):
    def testGradingTableView(self):
        response=self.c.get('/course/%u/gradingtable/'%self.course.pk)
        self.assertEquals(response.status_code, 200)

    def testDownloadArchiveView(self):
        response=self.c.get('/course/%u/archive/'%self.course.pk)
        self.assertEquals(response.status_code, 200)

    def testMailView(self):
        response=self.c.get('/course/%u/mail2all/'%self.course.pk)
        self.assertEquals(response.status_code, 200)

    def testNewAssignmentView(self):
        response=self.c.get('/teacher/opensubmit/assignment/add/')
        self.assertEquals(response.status_code, 200)

    def testNewCourseView(self):
        response=self.c.get('/teacher/opensubmit/course/add/')
        self.assertEquals(response.status_code, 200)

    def testPerfDataView(self):
        sub1 = self.createValidatedSubmission(self.current_user)
        sub2 = self.createValidatedSubmission(self.current_user)
        response=self.c.get('/assignments/%u/perftable/'%sub1.assignment.pk)
        # Resulting CSV should have header line + 2 result lines + empty final line
        self.assertEquals(len(response.content.split('\n')), 3+1)
        self.assertEquals(response.status_code, 200)
