import datetime
import logging

from django.conf import settings
from django.utils import timezone

from django.test import TestCase, LiveServerTestCase
from django.test.utils import override_settings
from django.test.client import Client

from django.contrib.auth.models import User
from django.contrib.auth.hashers import PBKDF2SHA1PasswordHasher

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile
from opensubmit.models import logger


class AnonStruct(object):
    def __init__(self, entries):
        self.__dict__.update(entries)


class FastPBKDF2SHA1PasswordHasher(PBKDF2SHA1PasswordHasher):
    iterations = 1

    
FAST_PASSWORD_HASHERS = (
    'opensubmit.tests.cases.FastPBKDF2SHA1PasswordHasher',
) + settings.PASSWORD_HASHERS


@override_settings(PASSWORD_HASHERS=FAST_PASSWORD_HASHERS)
class SubmitTestCase(LiveServerTestCase):
    current_user = None

    def createUser(self, user_dict):
        user_obj = User.objects.create_user(
            username=user_dict['username'],
            password=user_dict['password'],
            email=user_dict['email'],
        )

        if 'is_superuser' in user_dict:
            user_obj.is_superuser = user_dict['is_superuser']
        if 'is_staff' in user_dict:
            user_obj.is_staff = user_dict['is_staff']

        user_obj.save()
        user_profile = UserProfile(user=user_obj)
        user_profile.save()

        user_dict['user'] = user_obj
        user_dict['profile'] = user_profile
        user_struct = AnonStruct(user_dict)
        return user_struct

    def loginUser(self, user_struct):
        result = self.c.login(username=user_struct.username, password=user_struct.password)
        if result:
            self.current_user = user_struct
        return result

    def setUpUsers(self):
        self.c = Client()
        self.admin_dict = {
            'username': 'testrunner_admin',
            'password': 'PNZabhExaL6H',
            'email': 'testrunner_admin@django.localhost.local',
            'is_superuser': True,
            'is_staff': True,
        }
        self.admin = self.createUser(self.admin_dict)

        #TODO: This should happen automatically due to the post_save signal for User objects, but it doesn't in test runs
        from opensubmit.app import ensure_user_groups
        ensure_user_groups(self.admin.user, created = True)

        self.teacher_dict = {
            'username': 'testrunner_teacher',
            'password': '2tVvWzdknP56',
            'email': 'testrunner_teacher@django.localhost.local',
            'is_staff': True,
        }
        self.teacher = self.createUser(self.teacher_dict)

        self.another_teacher_dict = {
            'username': 'testrunner_anotherTeacher',
            'password': 'LW8vhgQWz5kT',
            'email': 'testrunner_anotherTeacher@django.localhost.local',
            'is_staff': True,
        }
        self.another_teacher = self.createUser(self.another_teacher_dict)

        self.tutor_dict = {
            'username': 'testrunner_tutor',
            'password': '2tVP56vMadkn',
            'email': 'testrunner_tutor@django.localhost.local',
            'is_staff': True,
        }
        self.tutor = self.createUser(self.tutor_dict)

        self.enrolled_students = list()
        for i in range(0, 5):
            enrolled_student_dict = {
                'username': 'testrunner_enrolled_student{}'.format(i),
                'password': 'very{}secret'.format(i),
                'email': 'testrunner_enrolled_student{}@django.localhost.local'.format(i),
            }
            self.enrolled_students.append(self.createUser(enrolled_student_dict))

        self.not_enrolled_students = list()
        for i in range(0, 5):
            not_enrolled_student_dict = {
                'username': 'testrunner_not_enrolled_student{}'.format(i),
                'password': 'not.very{}secret'.format(i),
                'email': 'testrunner_not_enrolled_student{}@django.localhost.local'.format(i),
            }
            self.not_enrolled_students.append(self.createUser(not_enrolled_student_dict))

    def setUpCourses(self):
        self.course = Course(
            title='Active test course',
            active=True,
            owner=self.teacher.user,
            max_authors=3,
        )
        self.course.save()
        self.course.tutors.add(self.tutor.user)
        for student in self.enrolled_students:
            self.course.participants.add(student.profile)
        
        self.anotherCourse = Course(
            title='Another active test course',
            active=True,
            owner=self.another_teacher.user,
            max_authors=1,
        )
        self.anotherCourse.save()
        
        self.inactiveCourse = Course(
            title='Inactive test course',
            active=False,
            owner=self.another_teacher.user,
            max_authors=1,
        )
        self.inactiveCourse.save()

    def setUpGradings(self):
        self.passGrade = Grading(title='passed', means_passed=True)
        self.passGrade.save()
        self.failGrade = Grading(title='failed', means_passed=False)
        self.failGrade.save()

        self.passFailGrading = GradingScheme(title='Pass/Fail Grading Scheme')
        self.passFailGrading.save()
        self.passFailGrading.gradings.add(self.passGrade)
        self.passFailGrading.gradings.add(self.failGrade)
        self.passFailGrading.save()

    def setUpAssignments(self):
        today = timezone.now()
        last_week = today - datetime.timedelta(weeks=1)
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(weeks=1)

        self.openAssignment = Assignment(
            title='Open assignment',
            course=self.course,
            download='http://example.org/assignments/1/download',
            gradingScheme=self.passFailGrading,
            publish_at=last_week,
            soft_deadline=tomorrow,
            hard_deadline=next_week,
            has_attachment=False,
        )
        self.openAssignment.save()

        self.softDeadlinePassedAssignment = Assignment(
            title='Soft deadline passed assignment',
            course=self.course,
            download='http://example.org/assignments/2/download',
            gradingScheme=self.passFailGrading,
            publish_at=last_week,
            soft_deadline=yesterday,
            hard_deadline=tomorrow,
            has_attachment=False,
        )
        self.softDeadlinePassedAssignment.save()

        self.hardDeadlinePassedAssignment = Assignment(
            title='Hard deadline passed assignment',
            course=self.course,
            download='http://example.org/assignments/3/download',
            gradingScheme=self.passFailGrading,
            publish_at=last_week,
            soft_deadline=yesterday,
            hard_deadline=yesterday,
            has_attachment=False,
        )
        self.hardDeadlinePassedAssignment.save()

        self.unpublishedAssignment = Assignment(
            title='Unpublished assignment',
            course=self.course,
            download='http://example.org/assignments/4/download',
            gradingScheme=self.passFailGrading,
            publish_at=tomorrow,
            soft_deadline=next_week,
            hard_deadline=next_week,
            has_attachment=False,
        )
        self.unpublishedAssignment.save()

    def setUp(self):
        super(SubmitTestCase, self).setUp()
        self.logger = logging.getLogger('OpenSubmit')
        self.loggerLevelOld = self.logger.level
        self.logger.setLevel(logging.WARN)
        self.setUpUsers()
        self.setUpCourses()
        self.setUpGradings()
        self.setUpAssignments()

    def tearDown(self):
        self.logger.setLevel(self.loggerLevelOld)

    def createSubmission(self, user, assignment, authors=[]):
        sub = Submission(
            assignment=assignment,
            submitter=user.user,
            notes="This is a submission.",
        )
        sub.save()

        if authors:
            [sub.authors.add(author) for author in authors]
        sub.save()

        return sub


class SubmitAdminTestCase(SubmitTestCase):
    def setUp(self):
        super(SubmitAdminTestCase, self).setUp()
        self.loginUser(self.admin)


class SubmitTeacherTestCase(SubmitTestCase):
    def setUp(self):
        super(SubmitTeacherTestCase, self).setUp()
        self.loginUser(self.teacher)


class SubmitTutorTestCase(SubmitTestCase):
    def setUp(self):
        super(SubmitTutorTestCase, self).setUp()
        self.loginUser(self.tutor)
