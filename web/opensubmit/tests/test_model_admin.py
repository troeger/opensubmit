'''
    Test cases focusing on the model admin extensions.
'''

from django import http
from django.contrib.admin.sites import AdminSite
from opensubmit.tests.cases import SubmitTutorTestCase, MockRequest
from opensubmit.models import Assignment, Course, SubmissionFile, Submission, GradingScheme
from opensubmit.admin.course import CourseAdmin

class ModelAdminTestCase(SubmitTutorTestCase):


    def testGradingBackend(self):
        from opensubmit.admin.grading import means_passed, grading_schemes
        self.assertEqual(means_passed(self.passGrade), True)
        self.assertEqual(means_passed(self.failGrade), False)
        self.assertEqual(grading_schemes(self.passGrade), self.passFailGrading.title)

    def testGradingsListFromGradingScheme(self):
        from opensubmit.admin.gradingscheme import gradings
        gradings_list = gradings(self.passFailGrading)
        assert(self.passGrade.title in gradings_list)
        assert(self.failGrade.title in gradings_list)

    def testCourseListFromGradingScheme(self):
        from opensubmit.admin.gradingscheme import courses
        course_list = courses(self.passFailGrading)
        assert(self.course.title in course_list)

    def testSubmissionFileBackend(self):
        from opensubmit.admin.submissionfile import SubmissionFileAdmin
        subfileadm = SubmissionFileAdmin(SubmissionFile, AdminSite())
        files_shown = subfileadm.get_queryset(self.request).count()
        self.assertEqual(0, files_shown)

    def testGradingSchemeAdminRendering(self):
        from opensubmit.admin.gradingscheme import GradingSchemeAdmin
        gsadmin = GradingSchemeAdmin(GradingScheme, AdminSite())
        assert('GradingSchemeForm' in str(gsadmin.get_form(self.request)))

    def testAssignmentBackend(self):
        from opensubmit.admin.assignment import AssignmentAdmin
        assadm = AssignmentAdmin(Assignment, AdminSite())
        assignments_shown = assadm.get_queryset(self.request).count()
        # should get all of them
        self.assertEqual(len(self.allAssignments), assignments_shown)

    def testCourseBackend(self):
        from opensubmit.admin.course import assignments as course_assignments
        courseadm = CourseAdmin(Course, AdminSite())
        num_courses = courseadm.get_queryset(self.request).count()
        self.assertEqual(num_courses, 1)
        ass_str_list = course_assignments(self.course)
        for ass in self.allAssignments:
            assert(ass.title in ass_str_list)

class SubmissionModelAdminTestCase(SubmitTutorTestCase):
    '''
        Test submission model admin functions, which needs more setUp
        than the other cases.
    '''
    def setUp(self):
        from opensubmit.admin.submission import SubmissionAdmin
        super(SubmissionModelAdminTestCase, self).setUp()
        self.sub1 = self.createSubmission(self.current_user, self.openAssignment)
        self.sub2 = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.val_sub = self.createValidatedSubmission(self.current_user)
        self.all_submissions = [self.sub1, self.sub2, self.val_sub]
        self.submadm = SubmissionAdmin(Submission, AdminSite())

    def testAuthorsFromSubmission(self):
        from opensubmit.admin.submission import authors
        assert(self.current_user.user.first_name in authors(self.sub1))

    def testSubmissionBackend(self):
        submissions = self.submadm.get_queryset(self.request)
        for sub in submissions:
            self.assertIn(sub, self.all_submissions)
        self.assertEqual(len(submissions), len(self.all_submissions))

    def testCloseAndNotify(self):
        from django.core import mail
        # Everything in status 'SUBMITTED', so no mail should be sent
        self.submadm.closeAndNotifyAction(self.request, Submission.objects.all())
        self.assertEqual(0, len(mail.outbox))
        # One mail should be sent
        self.sub1.state = Submission.GRADED
        self.sub1.save()
        self.sub2.state = Submission.GRADED
        self.sub2.save()        
        self.submadm.closeAndNotifyAction(self.request, Submission.objects.all())        
        self.assertEqual(2, len(mail.outbox))

    def testSetFullPendingAll(self):
        # Only one of the submission assignments has validation configured
        self.submadm.setFullPendingStateAction(self.request, Submission.objects.all())
        self.assertEqual(1, Submission.objects.filter(state=Submission.TEST_FULL_PENDING).count())

    def testSetFullPendingNoneMatching(self):
        # Only one of the submission assignments has validation configured
        self.submadm.setFullPendingStateAction(self.request, Submission.objects.filter(state=Submission.SUBMITTED))
        self.assertEqual(0, Submission.objects.filter(state=Submission.TEST_FULL_PENDING).count())

    def testSetInitialState(self):
        self.submadm.setInitialStateAction(self.request, Submission.objects.all())
        self.assertEqual(2, Submission.objects.filter(state=Submission.SUBMITTED).count())

    def testGradingNoteIndicator(self):
        from opensubmit.admin.submission import grading_notes
        self.assertEqual(False, grading_notes(self.sub1))
        self.sub1.grading_notes = 'Your are a bad student.'
        self.sub1.save()
        self.assertEqual(True, grading_notes(self.sub1))

    def testGradingFileIndicator(self):
        from django.core.files import File as DjangoFile
        from opensubmit.admin.submission import grading_file
        self.assertEqual(False, grading_file(self.sub1))
        self.sub1.grading_file = DjangoFile(open(__file__), str("grading_file.txt"))  
        self.sub1.save()
        self.assertEqual(True, grading_file(self.sub1))

    def testStateFilter(self):
        from opensubmit.admin.submission import SubmissionStateFilter
        submfilter = SubmissionStateFilter(self.request, {'statefilter': 'tobegraded'}, Submission, None)
        for sub in submfilter.queryset(self.request, Submission.objects.all()):
            assert(sub in self.all_submissions)
        graded_count = SubmissionStateFilter(self.request, {'statefilter': 'graded'}, Submission, None).queryset(self.request, Submission.objects.all()).count()
        self.assertEqual(graded_count, 0)

    def testAssignmentFilter(self):
        from opensubmit.admin.submission import SubmissionAssignmentFilter
        submfilter = SubmissionAssignmentFilter(self.request, {'assignmentfilter': self.sub1.assignment.pk}, Submission, None)
        sublist = submfilter.queryset(self.request, Submission.objects.all()).values_list('pk', flat=True)      
        self.assertSequenceEqual(sublist, [self.sub1.pk])


    def testCourseFilter(self):
        from opensubmit.admin.submission import SubmissionCourseFilter
        submfilter = SubmissionCourseFilter(self.request, {'coursefilter': self.course.pk}, Submission, None)
        subcount = submfilter.queryset(self.request, Submission.objects.all()).count()      
        self.assertEqual(subcount, len(self.all_submissions))

