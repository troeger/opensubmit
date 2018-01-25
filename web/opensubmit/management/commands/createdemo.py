import datetime
import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from opensubmit.models import Course, Assignment, Grading, GradingScheme, Submission, SubmissionFile, SubmissionTestResult, TestMachine
from opensubmit import settings
from django.utils import timezone
from django.core.files import File as DjangoFile
from tempfile import NamedTemporaryFile

# test machine
machine = TestMachine(
    last_contact=datetime.datetime.now(),
    host='UUID4711',
    config=json.dumps([["Operating system", "Plan 9"], ]))
machine.save()

def createSubmissionFile():
    with NamedTemporaryFile(mode="wt", delete=False, prefix=settings.MEDIA_ROOT) as tmpfile:
        # Submission file
        tmpfile.write("The quick brown fox jumps over the lazy dog.")
        tmpfile.close()
        sf = SubmissionFile(attachment=DjangoFile(tmpfile.name))
        sf.save()
        # os.remove(tmpfile.name)
        # Test results
        val_result = SubmissionTestResult()
        val_result.submission_file = sf
        val_result.kind = SubmissionTestResult.VALIDITY_TEST
        val_result.result = "Validation test result for student"
        val_result.result_tutor = "Validation test result for tutor"
        val_result.machine = machine
        val_result.save()
        full_result = SubmissionTestResult()
        full_result.submission_file = sf
        full_result.kind = SubmissionTestResult.FULL_TEST
        full_result.result_tutor = "Full test result for tutor"
        full_result.machine = machine
        full_result.save()
        return sf


class Command(BaseCommand):
    help = 'Creates demo data in the installation'

    def handle(self, *args, **options):

        print("Adding demo data ...")

        # create demo users
        users = {}
        for name in ['demo_student', 'demo_cheater', 'demo_tutor', 'demo_owner']:
            user = User.objects.filter(username=name).delete()
            user = User.objects.create_user(username=name,
                                            email='demo@example.org',
                                            password=name,
                                            first_name=name,
                                            last_name=name)
            users[name] = user

        # create demo grading
        Grading.objects.filter(title='passed (demo)').delete()
        passGrade = Grading(title='passed (demo)', means_passed=True)
        passGrade.save()
        Grading.objects.filter(title='failed (demo)').delete()
        failGrade = Grading(title='failed (demo)', means_passed=False)
        failGrade.save()
        GradingScheme.objects.filter(
            title='Pass/Fail Grading Scheme (Demo)').delete()
        passFailGrading = GradingScheme(
            title='Pass/Fail Grading Scheme (Demo)')
        passFailGrading.save()
        passFailGrading.gradings.add(passGrade)
        passFailGrading.gradings.add(failGrade)
        passFailGrading.save()

        # create demo course
        Course.objects.filter(title='Demo Course').delete()
        course = Course(
            title='Demo Course',
            active=True,
            owner=users['demo_owner'],
            homepage="http://www.open-submit.org"
        )
        course.save()
        course.tutors.add(users['demo_tutor'])
        course.participants.add(users['demo_student'].profile)
        course.participants.add(users['demo_cheater'].profile)

        today = timezone.now()
        last_week = today - datetime.timedelta(weeks=1)
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(weeks=1)

        # create demo assignment
        ass1 = Assignment(
            title='Demo A1: Graded group work with deadline',
            course=course,
            download='http://example.org/assignments1.pdf',
            gradingScheme=passFailGrading,
            publish_at=last_week,
            soft_deadline=tomorrow,
            hard_deadline=next_week,
            has_attachment=True,
            max_authors=3
        )
        ass1.save()

        # create demo assignment without grading
        ass2 = Assignment(
            title='Demo A2: Non-graded group work with deadline',
            course=course,
            download='http://example.org/assignments2.pdf',
            gradingScheme=None,
            publish_at=last_week,
            soft_deadline=tomorrow,
            hard_deadline=next_week,
            has_attachment=True,
            max_authors=3
        )
        ass2.save()

        # create demo assignment without deadlines
        ass3 = Assignment(
            title='Demo A3: Graded group work without deadline, only notes',
            course=course,
            download='http://example.org/assignments1.pdf',
            gradingScheme=passFailGrading,
            publish_at=last_week,
            soft_deadline=None,
            hard_deadline=None,
            has_attachment=False,
            max_authors=3
        )
        ass3.save()

        # create demo assignment without deadlines
        ass4 = Assignment(
            title='Demo A4: Graded group work with deadline being over',
            course=course,
            download='http://example.org/assignments1.pdf',
            gradingScheme=passFailGrading,
            publish_at=last_week,
            soft_deadline=last_week,
            hard_deadline=last_week,
            has_attachment=False,
            max_authors=3
        )
        ass4.save()

        # create demo submission
        Submission(
            assignment=ass1,
            submitter=users['demo_student'],
            notes="Demo submission for A1.",
            state=Submission.SUBMITTED_TESTED,
            file_upload=createSubmissionFile()
        ).save()

        # create cheater submission in course 1
        Submission(
            assignment=ass1,
            submitter=users['demo_cheater'],
            notes="Demo duplicate submission for A1.",
            state=Submission.SUBMITTED_TESTED,
            file_upload=createSubmissionFile()
        ).save()
