'''
    Tets cases focusing on the SubmissionFile model class methods.
'''

from opensubmit.tests.cases import SubmitTestCase

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile

class ModelSubmissionFileTestCase(SubmitTestCase):

    def prepareSubmission(self, fname1, fname2):
        '''
            Prepare two submissions with the given file uploads.
        '''
        f1 = self.createSubmissionFile(fname1);
        f2 = self.createSubmissionFile(fname2);
        sub1 = Submission(
            assignment=self.validatedAssignment,
            submitter=self.current_user.user,
            notes="This is a validatable submission.",
            state=Submission.TEST_COMPILE_PENDING,
            file_upload=f1
        )
        sub1.save()
        sub2 = Submission(
            assignment=self.validatedAssignment,
            submitter=self.current_user.user,
            notes="This is a validatable submission.",
            state=Submission.TEST_COMPILE_PENDING,
            file_upload=f2
        )
        sub2.save()
        return sub1, sub2

    def testMD5EqualArchiveFile(self):
        self.loginUser(self.enrolled_students[0])
        sub1=self.createValidatedSubmission(self.current_user)
        sub2=self.createValidatedSubmission(self.current_user)
        self.assertEqual(sub1.file_upload.md5, sub2.file_upload.md5)

    def testMD5EqualNonArchiveFile(self):
        self.loginUser(self.enrolled_students[0])
        sub1,sub2 = self.prepareSubmission("/opensubmit/static/social-buttons/auth-icons.png",
                                           "/opensubmit/static/social-buttons/auth-icons.png")
        self.assertEqual(sub1.file_upload.md5, sub2.file_upload.md5)

    def testMD5UequalNonArchiveFile(self):
        self.loginUser(self.enrolled_students[0])
        sub1,sub2 = self.prepareSubmission("/opensubmit/static/social-buttons/auth-icons.png",
                                           "/opensubmit/static/social-buttons/auth-buttons.css")
        self.assertNotEqual(sub1.file_upload.md5, sub2.file_upload.md5)


    def testMD5SimilarArchiveFile(self):
        self.loginUser(self.enrolled_students[0])
        sub1,sub2 = self.prepareSubmission("/opensubmit/tests/submfiles/working_withcode.zip",
                                           "/opensubmit/tests/submfiles/working_withcode_otherwhitespace.zip")
        self.assertEqual(sub1.file_upload.md5, sub2.file_upload.md5)

    def testMD5NonsimilarArchiveFile(self):
        self.loginUser(self.enrolled_students[0])
        sub1,sub2 = self.prepareSubmission("/opensubmit/tests/submfiles/working_withcode.zip",
                                           "/opensubmit/tests/submfiles/working_withsubdir.zip")
        self.assertNotEqual(sub1.file_upload.md5, sub2.file_upload.md5)
