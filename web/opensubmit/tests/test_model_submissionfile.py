'''
    Tets cases focusing on the SubmissionFile model class methods.
'''

from opensubmit.tests.cases import SubmitStudentTestCase

from .helpers.djangofiles import create_submission_file
from .helpers.assignment import create_validated_assignment_with_archive
from .helpers.assignment import create_pass_fail_grading
from .helpers.course import create_course
from .helpers.submission import create_validatable_submission
from .helpers.submission import create_validated_submission
from .helpers.user import create_user, admin_dict


class SubmissionFile(SubmitStudentTestCase):

    def setUp(self):
        super(SubmissionFile, self).setUp()

        # Prepare assignments
        self.admin = create_user(admin_dict)
        self.course = create_course(self.admin, self.user)
        self.grading_scheme = create_pass_fail_grading()
        self.assign = create_validated_assignment_with_archive(
            self.course, self.grading_scheme)

    def prepare_submission(self, fname1, fname2):
        '''
            Prepare two submissions with the given file uploads.
        '''
        f1 = create_submission_file(fname1)
        f2 = create_submission_file(fname2)
        sub1 = create_validatable_submission(self.user, self.assign, f1)
        sub2 = create_validatable_submission(self.user, self.assign, f2)
        return sub1, sub2

    def test_md5_equal_archive_file(self):
        sub1 = create_validated_submission(self.user, self.assign)
        sub2 = create_validated_submission(self.user, self.assign)
        self.assertEqual(sub1.file_upload.md5, sub2.file_upload.md5)

    def test_md5_equal_non_archive_file(self):
        sub1, sub2 = self.prepare_submission(
            "submfiles/duplicates/duplicate_orig.zip",
            "submfiles/duplicates/duplicate_orig.zip")
        self.assertEqual(sub1.file_upload.md5, sub2.file_upload.md5)

    def test_md5_uequal_non_archive_file(self):
        sub1, sub2 = self.prepare_submission(
            "submfiles/validation/1100ttf/validator.py",
            "submfiles/validation/1100ttf/packed.zip")
        self.assertNotEqual(sub1.file_upload.md5, sub2.file_upload.md5)

    def test_md5_similar_archive_file(self):
        sub1, sub2 = self.prepare_submission(
            "submfiles/duplicates/duplicate_copy.zip",
            "submfiles/duplicates/duplicate_orig.zip")
        self.assertEqual(sub1.file_upload.md5, sub2.file_upload.md5)

    def test_md5_nonsimilar_archive_file(self):
        sub1, sub2 = self.prepare_submission(
            "submfiles/duplicates/duplicate_copy.zip",
            "submfiles/validation/1000ttt/packed.tgz")
        self.assertNotEqual(sub1.file_upload.md5, sub2.file_upload.md5)
