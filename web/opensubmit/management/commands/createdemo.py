from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from opensubmit.models import Course, Assignment, UserProfile, Grading, GradingScheme, Submission
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Creates demo data in the installation'
    def handle(self, *args, **options):

        # create demo users
        users={}
        for name in ['demo_student', 'demo_tutor', 'demo_owner']:
            user=User.objects.filter(username=name).delete()
            user = User.objects.create_user( username=name,
                                             email='demo@example.org',
                                             password=name)
            users[name]=user

        # create demo grading
        passGrade = Grading(title='passed', means_passed=True)
        passGrade.save()
        failGrade = Grading(title='failed', means_passed=False)
        failGrade.save()
        passFailGrading = GradingScheme(title='Pass/Fail Grading Scheme (Demo)')
        passFailGrading.save()
        passFailGrading.gradings.add(passGrade)
        passFailGrading.gradings.add(failGrade)
        passFailGrading.save()

        # create demo course
        course = Course(
            title='Demo Course',
            active=True,
            owner=users['demo_owner'],
            max_authors=3,
        )
        course.save()
        course.tutors.add(users['demo_tutor'])
        course.participants.add(users['demo_student'].profile)

        today = timezone.now()
        last_week = today - datetime.timedelta(weeks=1)
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(weeks=1)

        # create demo assignment
        ass = Assignment(
            title='Demo Assignment 1',
            course=course,
            download='http://example.org/assignments1.pdf',
            gradingScheme=passFailGrading,
            publish_at=last_week,
            soft_deadline=tomorrow,
            hard_deadline=next_week,
            has_attachment=False
        )
        ass.save()

        # create demo assignment without grading
        ass2 = Assignment(
            title='Demo Assignment 2',
            course=course,
            download='http://example.org/assignments1.pdf',
            gradingScheme=None,
            publish_at=last_week,
            soft_deadline=tomorrow,
            hard_deadline=next_week,
            has_attachment=False
        )
        ass2.save()

        # create demo assignment without deadlines
        ass3 = Assignment(
            title='Demo Assignment 3',
            course=course,
            download='http://example.org/assignments1.pdf',
            gradingScheme=passFailGrading,
            publish_at=last_week,
            soft_deadline=None,
            hard_deadline=None,
            has_attachment=False
        )
        ass3.save()


        # create demo submission
        Submission(
            assignment=ass,
            submitter=users['demo_student'],
            notes="This is a demo submission.",
            state=Submission.SUBMITTED_TESTED
        ).save()

