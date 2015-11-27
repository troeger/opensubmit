'''
    Test cases for tutor 'GET' views and actions.
'''

from opensubmit.tests.cases import SubmitTutorTestCase
from opensubmit.models import SubmissionFile, Assignment
from django.contrib.admin.sites import AdminSite
from django.core.files import File

class TutorTestCaseSet():
    def testTeacherDashboardView(self):
        response=self.c.get('/teacher/')
        self.assertEquals(response.status_code, 200)

    def testAssignmentListBackend(self):
        from opensubmit.admin.assignment import AssignmentAdmin
        from opensubmit.admin.assignment import course as course_title
        assadm = AssignmentAdmin(Assignment, AdminSite())
        assignments_shown = assadm.get_queryset(self.request)
        for assignment in assignments_shown:
            self.assertEquals(assignment.course, self.course)
            self.assertEquals(course_title(assignment), self.course.title)

    def testSubmissionListView(self):
        response=self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 200)

    def testGradingTableView(self):
        response=self.c.get('/course/%u/gradingtable/'%self.course.pk)
        self.assertEquals(response.status_code, 200)

    def testPreviewView(self):
        sub1 = self.createValidatedSubmission(self.current_user)
        response=self.c.get('/preview/%u/'%sub1.pk)
        self.assertEquals(response.status_code, 200)

    def testPreviewBrokenView(self):
        '''
            Test proper handling of archives containing files with invalid unicode.
        '''
        sub1 = self.createValidatedSubmission(self.current_user)
        for fname in [u'broken_preview.gz', u'broken_preview2.gz', u'broken_preview.zip']:
            f=File(open(u"opensubmit/tests/submfiles/"+fname), fname)
            subfile = SubmissionFile()
            subfile.attachment=f
            subfile.save()
            sub1.file_upload=subfile
            sub1.save()
            response=self.c.get('/preview/%u/'%sub1.pk)
            self.assertEquals(response.status_code, 200)

class TutorTestCase(SubmitTutorTestCase, TutorTestCaseSet):
    '''
        Run the tests from the tutor case set as student tutor.
    '''
    def testCannotUseAdminBackend(self):
        '''
            Not in the test set above that is inherited for teacher and admin tests.
        '''
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 403)        # 302: can access the model in principle, 403: can never access the app label
