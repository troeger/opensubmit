'''
    Test cases for tutor 'GET' views and actions.
'''

from opensubmit.tests.cases import SubmitTutorTestCase
from opensubmit.models import SubmissionFile, Assignment, Submission
from django.contrib.admin.sites import AdminSite
from django.core.files import File

class TutorTestCase(SubmitTutorTestCase):
    def testTeacherDashboardView(self):
        response=self.c.get('/teacher/')
        self.assertEqual(response.status_code, 200)

    def testAssignmentListBackend(self):
        from opensubmit.admin.assignment import AssignmentAdmin
        from opensubmit.admin.assignment import course as course_title
        assadm = AssignmentAdmin(Assignment, AdminSite())
        assignments_shown = assadm.get_queryset(self.request)
        for assignment in assignments_shown:
            self.assertIn(assignment.course, self.all_courses)

    def testSubmissionListView(self):
        response=self.c.get('/teacher/opensubmit/submission/')
        self.assertEqual(response.status_code, 200)

    def testSubmissionEditView(self):
        sub = self.createValidatedSubmission(self.current_user)
        response=self.c.get('/teacher/opensubmit/submission/%u/change/'%sub.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(sub.get_validation_result().result))

    def testGradingTableView(self):
        response=self.c.get('/course/%u/gradingtable/'%self.course.pk)
        self.assertEqual(response.status_code, 200)

    def testDuplicateReportView(self):
        # Using this method twice generates a duplicate upload
        sub1 = self.createValidatableSubmission(self.enrolled_students[0])
        sub2 = create_validatable_submission(self.enrolled_students[1])
        sub3 = create_validatable_submission(self.enrolled_students[2])
        sub3.state=Submission.WITHDRAWN
        sub3.save()
        response=self.c.get('/assignments/%u/duplicates/'%self.validatedAssignment.pk)
        self.assertEqual(response.status_code, 200)
        # expect both submissions to be in the report
        self.assertIn('submission/%u/change'%sub1.pk, str(response.content))
        self.assertIn('submission/%u/change'%sub2.pk, str(response.content))
        # expect withdrawn submissions to be left out
        self.assertNotIn('#%u'%sub3.pk, str(response))

    def testPreviewView(self):
        sub1 = create_validated_submission(self.user)
        response=self.c.get('/preview/%u/'%sub1.pk)
        self.assertEqual(response.status_code, 200)

    def testPreviewBrokenView(self):
        '''
            Test proper handling of archives containing files with invalid unicode.
        '''
        sub1 = create_validated_submission(self.user)
        for fname in ['broken_preview.gz', 'broken_preview2.gz', 'broken_preview.zip']:
            subfile = self.createSubmissionFile("/opensubmit/tests/submfiles/"+fname)
            sub1.file_upload=subfile
            sub1.save()
            response=self.c.get('/preview/%u/'%sub1.pk)
            self.assertEqual(response.status_code, 200)

