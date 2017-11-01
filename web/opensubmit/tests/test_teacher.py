'''
    Test cases for teacher 'GET' views and actions. They include all cases for tutors by inheritance.
'''

import io, zipfile

from opensubmit.models import Submission
from .cases import SubmitTeacherTestCase
from .test_tutor import TutorTestCase
from django.contrib.auth.models import User

class TeacherTestCase(SubmitTeacherTestCase, TutorTestCase):
    def testNewAssignmentView(self):
        response=self.c.get('/teacher/opensubmit/assignment/add/')
        self.assertEqual(response.status_code, 200)

    def testEditAssignmentView(self):
        for ass in self.allAssignments:
            response=self.c.get('/teacher/opensubmit/assignment/%u/change/'%ass.pk)
            self.assertEqual(response.status_code, 200)

    def testGradingSchemeListView(self):
        response=self.c.get('/teacher/opensubmit/gradingscheme/')
        self.assertEqual(response.status_code, 200)

    def testGradingListView(self):
        response=self.c.get('/teacher/opensubmit/grading/')
        self.assertEqual(response.status_code, 200)

    def testAssignmentListView(self):
        response=self.c.get('/teacher/opensubmit/assignment/')
        self.assertEqual(response.status_code, 200)

    def testCourseListView(self):
        response=self.c.get('/teacher/opensubmit/course/')
        self.assertEqual(response.status_code, 200)

    def testGradingTableView(self):
        sub = self.createValidatedSubmission(self.current_user)
        sub.grading = self.passGrade
        sub.state = Submission.CLOSED
        sub.save()
        response = self.c.get('/course/%u/gradingtable/'%self.course.pk)
        self.assertEqual(response.status_code, 200)

    def testSubmissionFileListView(self):
        response=self.c.get('/teacher/opensubmit/submissionfile/')
        self.assertEqual(response.status_code, 200)

    def testMailView(self):
        response=self.c.get('/course/%u/mail2all/'%self.course.pk)
        self.assertEqual(response.status_code, 200)

    def testMailSending(self):
        # POST with parameters leads to preview, which stores relevant information in session
        response=self.c.post('/course/%u/mail2all/'%self.course.pk, {'subject': 'Foo', 'message': 'bar'})
        self.assertEqual(response.status_code, 200)
        # POST without parameters leads to sending of data stored in session
        # Expect redirect to overview
        response=self.c.post('/course/%u/mail2all/'%self.course.pk)
        self.assertEqual(response.status_code, 302)

    def testPerfDataView(self):
        sub1 = self.createValidatedSubmission(self.current_user)
        sub2 = self.createValidatedSubmission(self.current_user)
        response=self.c.get('/assignments/%u/perftable/'%sub1.assignment.pk)
        # Resulting CSV should have header line + 2 result lines + empty final line
        csv=response.content.decode(response.charset)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])        # content type
        self.assertEqual(len(csv.split('\n')), 3+1)

    def testCourseArchiveView(self):
        # add some student upload to be stored in the archive
        self.val_sub = self.createValidatedSubmission(self.current_user)
        response = self.c.get('/course/%u/archive/'%self.course.pk)
        self.assertEqual(response.status_code, 200)
        # Test if the download is really a ZIP file
        f = io.BytesIO(response.content)
        zipped_file = zipfile.ZipFile(f, 'r')
        try:
            # Check ZIP file validity
            self.assertIsNone(zipped_file.testzip())
            # Try to find a file some student stored in a sub-folder on it's own, targets #18
            found_stud_subfile = False
            for entry in zipped_file.filelist:
                if "student_folder/folder_in_folder/student_file_in_subfolder" in entry.filename:
                    found_stud_subfile = True
            assert(found_stud_subfile)
        finally:
            zipped_file.close()
            f.close()

    def testCourseArchiveWithNonZipView(self):
        # add some student upload to be stored in the archive
        self.val_sub = self.createValidatableNoArchiveSubmission(self.current_user)
        response = self.c.get('/course/%u/archive/'%self.course.pk)
        self.assertEqual(response.status_code, 200)

    def testAssignmentArchiveView(self):
        # add some student upload to be stored in the archive
        self.val_sub = self.createValidatedSubmission(self.current_user)
        response = self.c.get('/assignments/%u/archive/'%self.openAssignment.pk)
        self.assertEqual(response.status_code, 200)
        # Test if the download is really a ZIP file
        f = io.BytesIO(response.content)
        zipped_file = zipfile.ZipFile(f, 'r')
        try:
            # Check ZIP file validity
            self.assertIsNone(zipped_file.testzip())
        finally:
            zipped_file.close()
            f.close()

    def testAssignmentArchiveWithNonZipView(self):
        # add some student upload to be stored in the archive
        self.val_sub = self.createValidatableNoArchiveSubmission(self.current_user)
        response = self.c.get('/assignments/%u/archive/'%self.openAssignment.pk)
        self.assertEqual(response.status_code, 200)


    def testAddCourseTutorSignalHandler(self):
        # Add another tutor who had no backend rights before
        new_user = User(username='foo')
        new_user.save()
        assert(not new_user.is_staff)
        self.course.tutors.add(new_user)
        self.course.save()
        # Check if he got them afterwards
        new_user = User.objects.get(username='foo')
        assert(new_user.is_staff)

    def testRemoveCourseTutorSignalHandler(self):
        assert(self.tutor.user in self.course.tutors.all())
        assert(self.tutor.user.is_staff)
        self.course.tutors.remove(self.tutor.user)
        self.course.save()
        user = User.objects.get(username=self.tutor.username)
        assert(not user.is_staff)

    def testChangeCourseOwnerSignalHandler(self):
        # Get a course with some owner
        # Assign new owner who had no backend rights before
        new_owner = User(username='foo')
        new_owner.save()
        assert(not new_owner.is_staff)
        old_owner_name = self.course.owner.username
        self.course.owner = new_owner
        self.course.save()
        # Make sure the old one has no more rights
        old_owner = User.objects.get(username=old_owner_name)
        assert(not old_owner.is_staff)
        # Make sure the new one has now backend rights
        new_owner = User.objects.get(username='foo')
        assert(new_owner.is_staff)


