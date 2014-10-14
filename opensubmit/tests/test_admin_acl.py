from django.contrib.auth.models import User
from opensubmit.models import Assignment, Course, SubmissionFile
from opensubmit.tests.cases import MockRequest, SubmitAdminTestCase
from django.contrib.admin.sites import AdminSite

class AdminACLTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(AdminACLTestCase, self).setUp()

    def testCanUseTeacherBackend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 200)        

    def testCanUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 200)        

class BackendTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(BackendTestCase, self).setUp()

    def testAddCourseTutor(self):
        # Add another tutor who had no backend rights before
        new_user = User(username='foo')
        new_user.save()
        assert(not new_user.is_staff)
        self.course.tutors.add(new_user)
        self.course.save()
        # Check if he got them afterwards
        new_user = User.objects.get(username='foo')
        assert(new_user.is_staff)

    def testRemoveCourseTutor(self):
        # from test case setup
        assert(self.tutor.user in self.course.tutors.all())
        assert(self.tutor.user.is_staff)
        self.course.tutors.remove(self.tutor.user)
        self.course.save()
        user = User.objects.get(username=self.tutor.username)
        assert(not user.is_staff)

    def testChangeCourseOwner(self):
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

    def testAssignmentBackend(self):
        from opensubmit.admin.assignment import AssignmentAdmin
        assadm = AssignmentAdmin(Assignment, AdminSite())
        assignments_shown = assadm.get_queryset(self.request).count()
        # should get all of them
        self.assertEquals(len(self.allAssignments), assignments_shown)

    def testCourseBackend(self):
        from opensubmit.admin.course import CourseAdmin
        courseadm = CourseAdmin(Course, AdminSite())
        num_courses = courseadm.get_queryset(self.request).count()
        self.assertEquals(num_courses, len(self.all_courses))

    def testSubmissionFileBackend(self):
        from opensubmit.admin.submissionfile import SubmissionFileAdmin
        subfileadm = SubmissionFileAdmin(SubmissionFile, AdminSite())
        files_shown = subfileadm.get_queryset(self.request).count()
        self.assertEquals(0, files_shown)

