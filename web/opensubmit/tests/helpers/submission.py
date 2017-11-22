from opensubmit.tests import uccrap
from opensubmit.models import Submission

from .testmachine import create_test_machine
from .djangofiles import create_tested_submission_file


def create_submission(user, assignment):
    sub = Submission(
        assignment=assignment,
        submitter=user,
        notes=uccrap + "This is a submission.",
        state=Submission.SUBMITTED
    )
    sub.save()
    return sub


def create_validatable_submission(user, assignment, upload):
    '''
    Create a submission that is ready to be fetched.
    '''
    sub = Submission(
        assignment=assignment,
        submitter=user,
        notes="This is a validatable submission.",
        state=Submission.TEST_VALIDITY_PENDING,
        file_upload=upload
    )
    sub.save()
    return sub


def create_validated_submission(user, assignment, test_host='127.0.0.1'):
    '''
    Create a submission that already has test results in the database.
    '''
    machine = create_test_machine(test_host)
    sf = create_tested_submission_file(machine)
    sub = Submission(
        assignment=assignment,
        submitter=user,
        notes=uccrap + "This is an already validated submission.",
        state=Submission.SUBMITTED_TESTED,
        file_upload=sf
    )
    sub.save()
    return sub
