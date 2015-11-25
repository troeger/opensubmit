'''
    Tets cases focusing on the access rights of students.
'''

from opensubmit.tests.cases import *

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile

class StudentSubmissionWebTestCase(SubmitTestCase):
    def createSubmissions(self):
        self.openAssignmentSub = self.createSubmission(self.current_user, self.openAssignment)
        self.softDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.hardDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)
        
        self.submissions = (
            self.openAssignmentSub,
            self.softDeadlinePassedAssignmentSub,
            self.hardDeadlinePassedAssignmentSub,
        )


class StudentCreateSubmissionWebTestCase(StudentSubmissionWebTestCase):

    def testCanSubmit(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)
        cases = {
            self.openAssignment: (True, (200, 302, )),
            self.softDeadlinePassedAssignment: (True, (200, 302, )),
            self.hardDeadlinePassedAssignment: (False, (403, )),
            self.unpublishedAssignment: (False, (403, )),
        }
        for assignment in cases:
            response = self.c.post('/assignments/%s/new/' % assignment.pk, {
                'notes': 'This is a test submission.',
                'authors': str(submitter.user.pk)
            })
            expect_success, expected_responses = cases[assignment]
            self.assertIn(response.status_code, expected_responses)

            submission_exists = Submission.objects.filter(
                assignment__exact=assignment,
                submitter__exact=submitter.user,
            ).exists()
            self.assertEquals(submission_exists, expect_success)

    def testCanUpdate(self):
        submitter = self.enrolled_students[0]
        self.loginUser(submitter)

        # pending compilation, update not allowed
        sub = self.createValidatableSubmission(self.current_user)
        response = self.c.post('/update/%u/' % sub.pk)
        self.assertEquals(response.status_code, 400)

        # test successful, update not allowed
        sub = self.createValidatedSubmission(self.current_user)
        response = self.c.post('/update/%u/' % sub.pk)
        self.assertEquals(response.status_code, 400)

        # Move submission into valid state for re-upload
        sub.state = Submission.TEST_VALIDITY_FAILED
        sub.save()

        # Try to update file with invalid form data
        response = self.c.post('/update/%u/' % sub.pk, {'attachment':'bar'})   # invalid form data
        self.assertEquals(response.status_code, 200)    # render update view, again

        # Try to update file with correct POST data
        with open(rootdir+"/opensubmit/tests/submfiles/working_withsubdir.zip") as f:
            response = self.c.post('/update/%u/' % sub.pk, {'attachment': f})
            self.assertEquals(response.status_code, 302)    # redirect to dashboard after upload

    def testNonEnrolledCannotSubmit(self):
        submitter = self.not_enrolled_students[0]
        self.loginUser(submitter)
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This submission will fail because the user
                        is not enrolled in the course that the
                        assignment belongs to""",
            'authors': str(submitter.user.pk)
        })
        self.assertEquals(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=submitter.user,
            assignment__exact=self.openAssignment,
        ).count()
        self.assertEquals(submission_count, 0)

    def testCanSubmitAsTeam(self):
        self.loginUser(self.enrolled_students[0])
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.enrolled_students[1].user.pk),
        })
        self.assertIn(response.status_code, (200, 302, ))

        submission = Submission.objects.get(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.openAssignment,
        )
        self.assertTrue(submission.authors.filter(pk__exact=self.enrolled_students[1].user.pk).exists())

    def testCannotSubmitAsTeamWithoutEnrollment(self):
        self.loginUser(self.enrolled_students[0])
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.not_enrolled_students[0].user.pk),
        })
        self.assertEquals(response.status_code, 403)

        submission_count = Submission.objects.filter(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.openAssignment,
        ).count()
        self.assertEquals(submission_count, 0)

    def testCannotDoubleSubmitThroughTeam(self):
        submitter = self.enrolled_students[1]
        self.loginUser(submitter)
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This is an assignment that student1 has published.""",
            'authors': str(submitter.user.pk)
        })
        self.assertIn(response.status_code, (302, 200, ))

        first_submission_exists = Submission.objects.filter(
            submitter__exact=submitter.user,
            assignment__exact=self.openAssignment,
        ).exists()
        self.assertTrue(first_submission_exists)

        self.loginUser(self.enrolled_students[0])
        response = self.c.post('/assignments/%s/new/' % self.openAssignment.pk, {
            'notes': """This assignment is handed in by student0,
                        who collaborated with student1 on the
                        assignment.""",
            'authors': str(self.enrolled_students[1].user.pk),
        })
        self.assertEquals(response.status_code, 403)

        submission_exists = Submission.objects.filter(
            submitter__exact=self.enrolled_students[0].user,
            assignment__exact=self.openAssignment,
        ).exists()
        self.assertFalse(submission_exists)


class StudentWithdrawSubmissionWebTestCase(StudentSubmissionWebTestCase):
    def testCanWithdraw(self):
        self.loginUser(self.enrolled_students[0])

        self.createSubmissions()
        cases = {
            self.openAssignmentSub: (True, (200, 302, )),
            self.softDeadlinePassedAssignmentSub: (True, (200, 302, )),
            self.hardDeadlinePassedAssignmentSub: (False, (403, )),
        }
        for submission in cases:
            response = self.c.post('/withdraw/%s/' % submission.pk, {'confirm': '1', })
            expect_submission_withdrawn, expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)
            
            submission = Submission.objects.get(pk__exact=submission.pk)
            if expect_submission_withdrawn:
                self.assertEquals(submission.state, Submission.WITHDRAWN, submission)
            else:
                self.assertNotEqual(submission.state, Submission.WITHDRAWN, submission)

    def testCannotWithdrawOtherUsers(self):
        '''
            Create submissions as one user and check that another user cannot withdraw them.
        '''
        self.loginUser(self.enrolled_students[1])
        self.createSubmissions()

        self.loginUser(self.enrolled_students[0])
        cases = {
            self.openAssignmentSub: 403,
            self.softDeadlinePassedAssignmentSub: 403,
            self.hardDeadlinePassedAssignmentSub: 403,
        }
        for submission in cases:
            response = self.c.post('/withdraw/%s/' % submission.pk, {'confirm': '1', })
            self.assertEquals(response.status_code, cases[submission])
            submission = Submission.objects.get(pk__exact=submission.pk)
            self.assertNotEqual(submission.state, Submission.WITHDRAWN)

    def testCannotWithdrawGraded(self):
        self.loginUser(self.enrolled_students[0])

        for state in (Submission.GRADED, Submission.CLOSED, Submission.CLOSED_TEST_FULL_PENDING, ):
            sub = self.createSubmission(self.current_user, self.openAssignment)
            sub.state = state
            sub.save()

            response = self.c.post('/withdraw/%s/' % sub.pk, {'confirm': '1', })
            self.assertIn(response.status_code, (403, ))
            sub = Submission.objects.get(pk__exact=sub.pk)
            self.assertNotEqual(sub.state, Submission.WITHDRAWN)


class StudentShowSubmissionWebTestCase(StudentSubmissionWebTestCase):
    def testCanSee(self):
        self.loginUser(self.enrolled_students[0])

        self.createSubmissions()
        cases = {
            self.openAssignmentSub: (200, ),
            self.softDeadlinePassedAssignmentSub: (200, ),
            self.hardDeadlinePassedAssignmentSub: (200, ),
        }
        for submission in cases:
            response = self.c.get('/details/%s/' % submission.pk)
            expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)

    def testCannotSeeOtherUsers(self):
        self.loginUser(self.enrolled_students[1])
        self.createSubmissions()

        self.loginUser(self.enrolled_students[0])
        cases = {
            self.openAssignmentSub: (403, ),
            self.softDeadlinePassedAssignmentSub: (403, ),
            self.hardDeadlinePassedAssignmentSub: (403, ),
        }
        for submission in cases:
            response = self.c.get('/details/%s/' % submission.pk)
            expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)

class StudentACLTestCase(SubmitTestCase):
    def setUp(self):
        super(StudentACLTestCase, self).setUp()
        self.loginUser(self.enrolled_students[0])

    def createSubmissions(self):
        self.openAssignmentSub = self.createSubmission(self.current_user, self.openAssignment)
        self.softDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.hardDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)
        
        self.submissions = (
            self.openAssignmentSub,
            self.softDeadlinePassedAssignmentSub,
            self.hardDeadlinePassedAssignmentSub,
        )

    def testCanCreateSubmission(self):
        self.assertEquals(self.openAssignment.can_create_submission(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(self.current_user.user), True)

    def testCannotCreateSubmissionAfterDeadline(self):
        self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)

    def testCannotCreateSubmissionBeforePublishing(self):
        self.assertEquals(self.unpublishedAssignment.can_create_submission(self.current_user.user), False)

    def testAdminTeacherTutorAlwaysCanCreateSubmission(self):
        for user in (self.admin, self.teacher, self.tutor, ):
            self.assertEquals(self.openAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.unpublishedAssignment.can_create_submission(user.user), True)

    def testCannotDoubleSubmit(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.unpublishedAssignment.can_create_submission(self.current_user.user), False)

    def testCanWithdrawSubmission(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignmentSub.can_withdraw(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), True)

    def testCannotWithdrawSubmissionAfterDeadline(self):
        self.createSubmissions()
        self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), False)

    def testCanModifySubmission(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignmentSub.can_modify(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignmentSub.can_modify(self.current_user.user), True)

    def testCannotModifySubmissionAfterDeadline(self):
        self.createSubmissions()
        self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_modify(self.current_user.user), False)

    def testCanOrCannotReuploadSubmissions(self):
        self.createSubmissions()
        for state, desc in Submission.STATES:
            for submission in self.submissions:
                submission.state = state
                submission.save()

            # Submissions should only be allowed to be re-uploaded if:
            # 1. The code has already been uploaded and executed and
            # 2. the execution has failed, and
            # 3. the hard deadline has not passed.
            if state in (
                Submission.TEST_COMPILE_FAILED,
                Submission.TEST_VALIDITY_FAILED,
                Submission.TEST_FULL_FAILED,
            ):
                self.assertEquals(self.openAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEquals(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
            else:
                self.assertEquals(self.openAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEquals(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)

    def testCannotUseTeacherBackend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 302)        # 302: can access the model in principle, 403: can never access the app label

    def testCannotUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        #TODO: Still unclear why this is not raising 403 (see below)
        self.assertEquals(response.status_code, 302)        # 302: can access the model in principle, 403: can never access the app label

    def testCannotUseAdminBackendAsTutor(self):
        # Assign rights
        self.course.tutors.add(self.current_user.user)
        self.course.save()
        # Admin access should be still forbidden
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 403)        # 302: can access the model in principle, 403: can never access the app label

    def testStudentBecomesTutor(self):
        # Before rights assignment        
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 302)        # 302: can access the model in principle, 403: can never access the app label
        # Assign rights
        self.course.tutors.add(self.current_user.user)
        self.course.save()
        # After rights assignment
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 200)        # Access allowed
        # Take away rights
        self.course.tutors.remove(self.current_user.user)
        self.course.save()
        # After rights removal
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 302)        # 302: can access the model in principle, 403: can never access the app label

    def testCannotUseAdminBackendAsCourseOwner(self):
        # Assign rights
        self.course.owner = self.current_user.user
        self.course.save()
        # Admin access should be still forbidden
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 403)        # 302: can access the model in principle, 403: can never access the app label

    def testStudentBecomesCourseOwner(self):
        # Before rights assignment        
        response = self.c.get('/teacher/opensubmit/course/%u/'%(self.course.pk))
        self.assertEquals(response.status_code, 302)        # 302: can access the model in principle, 403: can never access the app label
        # Assign rights
        old_owner = self.course.owner
        self.course.owner = self.current_user.user
        self.course.save()
        # After rights assignment
        response = self.c.get('/teacher/opensubmit/course/%u/'%(self.course.pk))
        self.assertEquals(response.status_code, 200)        
        # Take away rights
        self.course.owner = old_owner
        self.course.save()
        # After rights removal
        response = self.c.get('/teacher/opensubmit/course/%u/'%(self.course.pk))
        self.assertEquals(response.status_code, 302)        # 302: can access the model in principle, 403: can never access the app label

