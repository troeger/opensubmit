from opensubmit import settings
from opensubmit.tests import uccrap, rootdir
from opensubmit.models import Assignment, Grading, GradingScheme

from .djangofiles import create_description_file

from django.utils import timezone
from django.core.files import File as DjangoFile

import datetime
import shutil


today = timezone.now()
last_week = today - datetime.timedelta(weeks=1)
yesterday = today - datetime.timedelta(days=1)
tomorrow = today + datetime.timedelta(days=1)
next_week = today + datetime.timedelta(weeks=1)


def create_pass_fail_grading():
    pass_grade = Grading(title=uccrap + 'passed', means_passed=True)
    pass_grade.save()
    fail_grade = Grading(title=uccrap + 'failed', means_passed=False)
    fail_grade.save()

    pass_fail_grading = GradingScheme(title=uccrap + 'Pass/Fail')
    pass_fail_grading.save()
    pass_fail_grading.gradings.add(pass_grade)
    pass_fail_grading.gradings.add(fail_grade)
    pass_fail_grading.save()

    return pass_fail_grading


def create_open_assignment(course, grading_scheme, authors=3):
    assign = Assignment(
        title=uccrap + 'Open assignment',
        course=course,
        download='http://example.org/assignments/1/download' + uccrap,
        gradingScheme=grading_scheme,
        publish_at=last_week,
        soft_deadline=tomorrow,
        hard_deadline=next_week,
        has_attachment=False,
        max_authors=authors
    )
    assign.save()
    return assign


def create_uploaded_desc_assignment(course, grading_scheme):
    assign = Assignment(
        title=uccrap + 'Open assignment with uploaded description file',
        course=course,
        download=None,
        description=create_description_file(),
        gradingScheme=grading_scheme,
        publish_at=last_week,
        soft_deadline=tomorrow,
        hard_deadline=next_week,
        has_attachment=False,
        max_authors=3
    )
    assign.save()
    return assign


def create_no_hard_soft_passed_assignment(course, grading_scheme):
    assign = Assignment(
        title=uccrap + 'No hard soft passed deadline assignment',
        course=course,
        download='http://example.org/assignments/1/download' + uccrap,
        gradingScheme=grading_scheme,
        publish_at=last_week,
        soft_deadline=yesterday,
        hard_deadline=None,
        has_attachment=False,
        max_authors=3
    )
    assign.save()
    return assign


def create_no_grading_assignment(course):
    assign = Assignment(
        title=uccrap + 'No grading assignment',
        course=course,
        download='http://example.org/assignments/1/download' + uccrap,
        gradingScheme=None,
        publish_at=last_week,
        soft_deadline=tomorrow,
        hard_deadline=next_week,
        has_attachment=False,
        max_authors=3
    )
    assign.save()
    return assign


def create_unpublished_assignment(course, grading_scheme):
    assign = Assignment(
        title=uccrap + 'Unpublished assignment',
        course=course,
        download='http://example.org/assignments/1/download' + uccrap,
        gradingScheme=grading_scheme,
        publish_at=tomorrow,
        soft_deadline=next_week,
        hard_deadline=next_week,
        has_attachment=False,
        max_authors=3
    )
    assign.save()
    return assign


def create_file_assignment(course, grading_scheme):
    assign = Assignment(
        title=uccrap + 'File assignment',
        course=course,
        download='http://example.org/assignments/1/download' + uccrap,
        gradingScheme=grading_scheme,
        publish_at=last_week,
        soft_deadline=tomorrow,
        hard_deadline=next_week,
        has_attachment=True,
        max_authors=3
    )
    assign.save()
    return assign


def create_soft_passed_assignment(course, grading_scheme):
    assign = Assignment(
        title=uccrap + 'Soft deadline passed assignment',
        course=course,
        download='http://example.org/assignments/2/download' + uccrap,
        gradingScheme=grading_scheme,
        publish_at=last_week,
        soft_deadline=yesterday,
        hard_deadline=tomorrow,
        has_attachment=False,
        max_authors=3
    )
    assign.save()
    return assign


def create_hard_passed_assignment(course, grading_scheme):
    assign = Assignment(
        title=uccrap + 'Hard deadline passed assignment',
        course=course,
        download='http://example.org/assignments/2/download' + uccrap,
        gradingScheme=grading_scheme,
        publish_at=last_week,
        soft_deadline=yesterday,
        hard_deadline=yesterday,
        has_attachment=False,
        max_authors=3
    )
    assign.save()
    return assign


def create_validated_assignment_with_archive(course, grading_scheme):
    # Move test files to current MEDIA_ROOT,
    # otherwise Django security complains
    source = rootdir + 'submfiles/validation/1000tft/packed.zip'
    dest_submission = settings.MEDIA_ROOT + "packed.zip"
    shutil.copyfile(source, dest_submission)
    source = rootdir + 'submfiles/validation/1000tft/validator.zip'
    dest_validator = settings.MEDIA_ROOT + "validator.zip"
    shutil.copyfile(source, dest_validator)

    with open(dest_validator, 'rb') as validator_script:
        assign = Assignment(
            title=uccrap + 'Validated assignment',
            course=course,
            download='http://example.org/assignments/1/download' + uccrap,
            gradingScheme=grading_scheme,
            publish_at=last_week,
            soft_deadline=tomorrow,
            hard_deadline=next_week,
            has_attachment=True,
            validity_script_download=True,
            attachment_test_validity=DjangoFile(validator_script),
            attachment_test_full=DjangoFile(validator_script),
            max_authors=3
        )
        assign.save()
        return assign


def create_validated_assignment_with_file(course, grading_scheme):
    # Move test files to current MEDIA_ROOT,
    # otherwise Django security complains
    source = rootdir + 'submfiles/validation/1000tff/packed.zip'
    dest_submission = settings.MEDIA_ROOT + "packed.zip"
    shutil.copyfile(source, dest_submission)
    source = rootdir + 'submfiles/validation/1000tff/validator.py'
    dest_validator = settings.MEDIA_ROOT + "validator.py"
    shutil.copyfile(source, dest_validator)

    with open(dest_validator, 'rb') as validator_script:
        assign = Assignment(
            title=uccrap + 'Validated assignment',
            course=course,
            download='http://example.org/assignments/1/download' + uccrap,
            gradingScheme=grading_scheme,
            publish_at=last_week,
            soft_deadline=tomorrow,
            hard_deadline=next_week,
            has_attachment=True,
            validity_script_download=True,
            attachment_test_validity=DjangoFile(validator_script),
            attachment_test_full=DjangoFile(validator_script),
            max_authors=3
        )
        assign.save()
        return assign

def create_all_assignments(course, grading_scheme):
    return [create_validated_assignment_with_archive(course, grading_scheme),
            create_validated_assignment_with_file(course, grading_scheme),
            create_file_assignment(course, grading_scheme),
            create_soft_passed_assignment(course, grading_scheme).
            create_uploaded_desc_assignment(course, grading_scheme),
            create_hard_passed_assignment(course, grading_scheme),
            create_no_hard_soft_passed_assignment(course, grading_scheme),
            create_unpublished_assignment(course, grading_scheme),
            create_open_assignment(course, grading_scheme),
            create_open_assignment(course, grading_scheme, authors=1),
            ]
