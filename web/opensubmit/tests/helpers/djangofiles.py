from opensubmit.tests import uccrap, rootdir
from opensubmit.models import SubmissionTestResult, SubmissionFile

from django.core.files import File as DjangoFile

import datetime
import os.path


def create_description_file(relpath="/submfiles/validation/0100fff/python.pdf"):
    return DjangoFile(open(rootdir + relpath, 'rb'),
                      str(datetime.datetime.now()))


def create_submission_file(relpath="/submfiles/validation/1000ttt/packed.tgz"):
    '''
    Several test cases assume a packed submission with subdirs,
    so the default above is intentional.
    '''
    with open(rootdir + relpath, 'rb') as subfile:
        sf = SubmissionFile(
            attachment=DjangoFile(subfile, str(datetime.datetime.now())),
            original_filename=os.path.basename(relpath)
        )
        sf.save()
    return sf


def create_tested_submission_file(test_machine):
    '''
    Create finalized test result in the database.
    '''
    sf = create_submission_file()
    SubmissionTestResult(
        kind=SubmissionTestResult.VALIDITY_TEST,
        result=uccrap + "Validation ok.",
        machine=test_machine,
        perf_data=uccrap + ";41;42;43",
        submission_file=sf).save()
    SubmissionTestResult(
        kind=SubmissionTestResult.FULL_TEST,
        result=uccrap + "Full test ok.",
        perf_data=uccrap + ";77;88;99",
        machine=test_machine,
        submission_file=sf).save()
    return sf
