from django.test import LiveServerTestCase
from django.test.client import Client
from submit.models import Course, Submission

class SubmitTestCase(LiveServerTestCase):
    def setUp(self):
        self.c=Client()
        self.c.login(username='testadmin', password='testadmin') 

    def createCourse(self, title):
        return self.c.post('/admin/submit/course/add/', 
            {'title': title,
             'owner': self.userid,
             'tutors': self.userid,
             'homepage': 'www.heise.de',
             'active': 'on',
             'max_authors': 3})

    def createGrading(self, title, means_passed):
        return self.c.post('/admin/submit/grading/add/', 
            {'title': title,
             'means_passed': str(means_passed)})

    def createSubmission(self, assignment, notes):
        return self.c.post('/assignments/%s/new'%assignment, 
            {'notes': notes})

class BasicTestCase(SubmitTestCase):
    fixtures = ['empty.json']
    userid = 1  # from fixture

    def testDashboardRedirect(self):
        response=self.c.get('/')
        self.assertEqual(response.status_code, 302)
        assert(response['Location'].endswith('/dashboard/'))

    def testCourseCreation(self):
        response = self.createCourse('Test Course')
        self.assertEqual(response.status_code, 302)
        assert(Course.objects.get(title='Test Course'))

    def testGradingCreation(self):
        for title, passed in [['Passed', True], ['Failed', False]]:
            response = self.createGrading(title, passed)
            self.assertEqual(response.status_code, 302)

class RulesTestCase(SubmitTestCase):
    fixtures = ['test.json']
    user_id = 1
    course_id = 1
    assignment_id = 1

    def testLateSubmission(self):
        ''' The deadline date in the fixture is always over, so we
            do not need to change anything here.
        '''
        response = self.createSubmission(self.assignment_id, 'My solution')
        self.assertEqual(response.status_code, 301)
        assert(Submission.objects.all().count() == 0)

