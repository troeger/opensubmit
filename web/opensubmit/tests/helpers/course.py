from opensubmit.tests import uccrap
from opensubmit.models import Course


def create_course(owner, tutor=None, students=None):
    c = Course(
        title=uccrap + 'Active test course',
        active=True,
        owner=owner
    )
    c.save()
    if tutor:
        c.tutors.add(tutor)
    if students:
        for student in students:
            c.participants.add(student.profile)
    return c
