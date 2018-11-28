'''
    Tets cases focusing on the frontend views ('GET') accessed by students.
'''

from django.contrib.auth.models import User
from lti import ToolConsumer

from opensubmit.tests.cases import SubmitStudentScenarioTestCase
from .helpers.user import get_student_dict
from .helpers.submission import create_validated_submission
from .helpers.testmachine import create_test_machine


class Student(SubmitStudentScenarioTestCase):
    def test_assignment_description_url_on_dashboard(self):
        self.create_submissions()
        response = self.c.get('/dashboard/')
        # Check for assignment description links of open assignments
        for assignment in self.all_assignments:
            if assignment.can_create_submission(self.user):
                self.assertContains(response, "http://")
        # Check for assignment description links of active submissions
        for sub in self.submissions:
            self.assertContains(response, "http://")

    def test_can_see_submissions(self):
        self.create_submissions()
        cases = {
            self.open_assignment_sub: (200, ),
            self.soft_deadline_passed_assignment_sub: (200, ),
            self.hard_deadline_passed_assignment_sub: (200, ),
        }
        for submission in cases:
            response = self.c.get('/details/%s/' % submission.pk)
            expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)

    def test_validation_result_rendering(self):
        sub = create_validated_submission(self.user, self.open_file_assignment)
        response = self.c.get('/details/%s/' % sub.pk)
        assert(sub.get_validation_result().result)
        # Search for headline
        self.assertContains(response, "Validity test result:")
        # Search for content
        self.assertContains(response, sub.get_validation_result().result)

    def test_can_see_only_enabled_course_assignments(self):
        # One default course registration in cases.py
        assignments_before = len(self.user.profile.open_assignments())
        # Become part of another course
        self.another_course.participants.add(self.user.profile)
        assignments_after = len(self.user.profile.open_assignments())
        self.assertNotEqual(assignments_before, assignments_after)

    def test_enable_course_with_get_in_dashboard_url(self):
        student = self.user

        # One default course registration in cases.py
        assignments_before = len(student.profile.open_assignments())

        # Provide GET parameter to enable course to root dir, which performs
        # a redirection to the dashboard
        response = self.c.get('/dashboard/?course=%u' % self.another_course.pk)
        self.assertEqual(response.status_code, 200)

        # Check if course is enabled now, based on assignment count
        assignments_after = len(student.profile.open_assignments())
        self.assertNotEqual(assignments_before, assignments_after)

    def test_enable_course_with_get_in_root_url(self):
        student = self.user

        # One default course registration in cases.py
        assignments_before = len(student.profile.open_assignments())

        # Provide GET parameter to enable course to root dir, which performs
        # a redirection to the dashboard
        response = self.c.get('/?course=%u' %
                              self.another_course.pk, follow=True)
        self.assertRedirects(response, '/dashboard/')

        # Check if course is enabled now, based on assignment count
        assignments_after = len(student.profile.open_assignments())
        self.assertNotEqual(assignments_before, assignments_after)

    def test_enable_course_with_get_for_fresh_user(self):
        student = self.user

        student.first_name = ""
        student.save()

        # One default course registration in cases.py
        assignments_before = len(student.profile.open_assignments())
        self.assertEqual(assignments_before,
                         len(self.all_student_visible_assignments))

        # Go to root URL with course demand,
        # message for missing details should show up
        response = self.c.get('/?course=%u' %
                              self.another_course.pk, follow=True)
        self.assertContains(response, "incomplete")

        # Check if course is enabled now, based on assignment count
        assignments_after = len(student.profile.open_assignments())
        self.assertNotEqual(assignments_before, assignments_after)

    def test_cannot_see_other_users(self):
        self.create_submissions()
        self.create_and_login_user(get_student_dict(1))
        cases = {
            self.open_assignment_sub: (403, ),
            self.soft_deadline_passed_assignment_sub: (403, ),
            self.hard_deadline_passed_assignment_sub: (403, ),
        }
        for submission in cases:
            response = self.c.get('/details/%s/' % submission.pk)
            expected_responses = cases[submission]
            self.assertIn(response.status_code, expected_responses)

    def test_index_view(self):
        # User is already logged in, expecting dashboard redirect
        response = self.c.get('/')
        self.assertEqual(response.status_code, 302)

    def test_index_without_login_view(self):
        self.c.logout()
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        # User is already logged in, expecting redirect
        response = self.c.get('/logout/')
        self.assertEqual(response.status_code, 302)

    def test_new_submission_view(self):
        response = self.c.get('/assignments/%s/new/' % self.open_assignment.pk)
        self.assertEqual(response.status_code, 200)

    def test_settings_view(self):
        response = self.c.get('/settings/')
        self.assertEqual(response.status_code, 200)
        # Send new data, saving should redirect to dashboard
        response = self.c.post('/settings/',
                               {'username': 'foobar',
                                'first_name': 'Foo',
                                'last_name': 'Bar',
                                'email': 'foo@bar.eu'}
                               )
        self.assertEqual(response.status_code, 302)
        u = User.objects.get(pk=self.user.pk)
        self.assertEqual(u.username, 'foobar')

    def test_courses_view(self):
        response = self.c.get('/courses/')
        self.assertEqual(response.status_code, 200)

    def test_change_courses_view(self):
        response = self.c.get('/courses/')
        self.assertEqual(response.status_code, 200)
        # Send new data, saving should redirect to dashboard
        course_ids = [str(self.course.pk), str(self.another_course.pk)]
        response = self.c.post('/courses/', {'courses': course_ids})
        self.assertEqual(response.status_code, 302)

    def test_enforced_user_settings_view(self):
        self.user.first_name = ""
        self.user.save()
        response = self.c.get('/dashboard/')
        self.assertContains(response, "incomplete")

    def test_dashboard_view(self):
        response = self.c.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_machine_view(self):
        machine = create_test_machine('127.0.0.1')
        response = self.c.get('/machine/%u/' % machine.pk)
        self.assertEqual(response.status_code, 200)

    def test_cannot_use_teacher_backend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        # 302: can access the model in principle
        # 403: can never access the app label
        self.assertEqual(response.status_code, 302)

    def test_student_becomes_course_owner_by_signal(self):
        # Before rights assignment
        response = self.c.get(
            '/teacher/opensubmit/course/%u/change/' % (self.course.pk))
        # 302: can access the model in principle
        # 403: can never access the app label
        self.assertEqual(response.status_code, 302)
        # Assign rights
        old_owner = self.course.owner
        self.course.owner = self.user
        self.course.save()
        # After rights assignment
        response = self.c.get(
            '/teacher/opensubmit/course/%u/change/' % (self.course.pk))
        self.assertEqual(response.status_code, 200)
        # Take away rights
        self.course.owner = old_owner
        self.course.save()
        # After rights removal
        response = self.c.get(
            '/teacher/opensubmit/course/%u/change/' % (self.course.pk))
        # 302: can access the model in principle
        # 403: can never access the app label
        self.assertEqual(response.status_code, 302)

    def test_student_becomes_tutor(self):
        # Before rights assignment
        response = self.c.get('/teacher/opensubmit/submission/')
        # 302: can access the model in principle
        # 403: can never access the app label
        self.assertEqual(response.status_code, 302)
        # Assign rights
        self.course.tutors.add(self.user)
        self.course.save()
        # After rights assignment
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEqual(response.status_code, 200)        # Access allowed
        # Take away rights
        self.course.tutors.remove(self.user)
        self.course.save()
        # After rights removal
        response = self.c.get('/teacher/opensubmit/submission/')
        # 302: can access the model in principle
        # 403: can never access the app label
        self.assertEqual(response.status_code, 302)

    def test_lti_config_info(self):
        response = self.c.get('/assignments/%s/lti/' % self.open_assignment.pk)
        self.assertEqual(response.status_code, 200)

    # Only works overy HTTPS, which is not given by the test server
    # def test_working_lti_credentials(self):
    #     url = "http://testserver/assignments/%s/lti/" % self.open_assignment.pk

    #     consumer = ToolConsumer(
    #         consumer_key=self.course.lti_key,
    #         consumer_secret=self.course.lti_secret,
    #         launch_url=url,
    #         params={
    #             'lti_message_type': 'basic-lti-launch-request',
    #             'resource_link_id': 1
    #         }
    #     )

    #     response = self.c.post(url, consumer.generate_launch_data())
    #     self.assertEqual(302, response.status_code)

    def test_wrong_lti_credentials(self):
        url = "http://testserver/assignments/%s/lti/" % self.open_assignment.pk

        consumer = ToolConsumer(
            consumer_key="awilfhawilejfhcbawiehjbcfaliejkwf",
            consumer_secret="awhlöfhjawköfjhawökefhjwaölkefrk",
            launch_url=url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'resource_link_id': 1
            }
        )

        response = self.c.post(url, consumer.generate_launch_data())
        self.assertEqual(403, response.status_code)
