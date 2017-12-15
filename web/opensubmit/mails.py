from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse

from opensubmit import settings


STUDENT_FAILED_SUB = 'Warning - Validation failed'

STUDENT_FAILED_MSG = '''
Hi,

this is a short notice that your submission for "%s" in "%s"
failed in the automated validation test.

Further information can be found at %s.'''

STUDENT_PASSED_SUB = 'Validation successful'

STUDENT_PASSED_MSG = '''
Hi,

this is a short notice that your submission for "%s" in "%s"
passed in the automated validation test.

Further information can be found at %s.'''

STUDENT_GRADED_SUB = 'Grading finished'

STUDENT_GRADED_MSG = '''
Hi,

this is a short notice that the of grading your submission
for "%s" in "%s" was finalized.

Further information can be found at %s.'''


def inform_student(submission, state):
    '''
    Create an email message for the student,
    based on the given submission state.

    Sending eMails on validation completion does
    not work, since this may have been triggered
    by the admin.
    '''
    details_url = settings.MAIN_URL + reverse('details', args=(submission.pk,))

    if state == submission.TEST_VALIDITY_FAILED:
        subject = STUDENT_FAILED_SUB
        message = STUDENT_FAILED_MSG
        message = message % (submission.assignment,
                             submission.assignment.course,
                             details_url)

    elif state == submission.CLOSED:
        if submission.assignment.is_graded():
            subject = STUDENT_GRADED_SUB
            message = STUDENT_GRADED_MSG
        else:
            subject = STUDENT_PASSED_SUB
            message = STUDENT_PASSED_MSG
        message = message % (submission.assignment,
                             submission.assignment.course,
                             details_url)
    else:
        return

    subject = "[%s] %s" % (submission.assignment.course, subject)
    from_email = submission.assignment.course.owner.email
    recipients = submission.authors.values_list(
        'email', flat=True).distinct().order_by('email')
    # send student email with BCC to course owner.
    # TODO: This might be configurable later
    # email = EmailMessage(subject, message, from_email, recipients,
    # [self.assignment.course.owner.email])
    email = EmailMessage(subject, message, from_email, recipients)
    email.send(fail_silently=True)
