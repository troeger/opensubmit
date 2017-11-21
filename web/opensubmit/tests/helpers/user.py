'''
Helpers for the test suite that deal with users.
'''

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from opensubmit.models import UserProfile
from opensubmit.tests import uccrap

admin_dict = {
    'username': uccrap + 'testrunner_admin',
    'password': uccrap + 'PNZabhExaL6H',
    'email': uccrap + 'testrunner_admin@django.localhost.local',
    'is_staff': True,
    'is_superuser': True
}

teacher_dict = {
    'username': uccrap + 'testrunner_teacher',
    'password': uccrap + '2tVvWzdknP56',
    'email': uccrap + 'testrunner_teacher@django.localhost.local',
    'is_staff': True,
    'is_superuser': False
}

another_teacher_dict = {
    'username': uccrap + 'testrunner_anotherTeacher',
    'password': uccrap + 'LW8vhgQWz5kT',
    'email': uccrap + 'testrunner_anotherTeacher@django.localhost.local',
    'is_staff': True,
    'is_superuser': False
}

tutor_dict = {
    'username': uccrap + 'testrunner_tutor',
    'password': uccrap + '2tVP56vMadkn',
    'email': uccrap + 'testrunner_tutor@django.localhost.local',
    'is_staff': True,
    'is_superuser': False
}

enrolled_students_dict = list()
for i in range(0, 5):
    enrolled_student_dict = {
        'username': uccrap + 'testrunner_enrolled_student{}'.format(i),
        'password': uccrap + 'very{}secret'.format(i),
        'email': uccrap +
        'testrunner_enrolled_student{}@django.localhost.local'.format(i),
        'is_staff': False,
        'is_superuser': False,
        'first_name': uccrap + 'Harold',
        'last_name': uccrap + 'Finch'
    }
    enrolled_students_dict.append(enrolled_student_dict)

not_enrolled_students_dict = list()
for i in range(0, 5):
    not_enrolled_student_dict = {
        'username': uccrap + 'testrunner_not_enrolled_student{}'.format(i),
        'password': uccrap + 'not.very{}secret'.format(i),
        'email': uccrap +
        'testrunner_not_enrolled_student{}@django.localhost.local'.format(i),
        'is_staff': False,
        'is_superuser': False
    }
    not_enrolled_students_dict.append(not_enrolled_student_dict)


class AnonStruct(object):
    def __init__(self, entries):
        self.__dict__.update(entries)


def create_user(user_dict):
    args = dict(user_dict)
    args['password'] = make_password(args['password'])
    user_obj = User(**args)
    user_obj.save()

    UserProfile.objects.get_or_create(user=user_obj)
    return user_obj
