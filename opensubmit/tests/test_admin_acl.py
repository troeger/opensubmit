from opensubmit.tests.cases import *

class AdminACLTestCase(SubmitAdminTestCase):
    def setUp(self):
        super(AdminACLTestCase, self).setUp()

    def testCanUseTeacherBackend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 200)        

    def testCanUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 200)        

    def testAddCourseTutor(self):
    	# Get a course

    	# Add another tutor who had no backend rights before

    	# Check if he got them afterwards

    def testRemoveCourseTutor(self):
    	# Get a course with a tutor

    	# Remove him so that he has no more backend rights

    	# Check if they were removed accordingly

    def testChangeCourseOwner(self):
    	# Get a course with some owner

    	# Assign new owner who had no backend rights before

    	# Make sure the old one has no more rights

    	# Make sure the new one has now backend rights

