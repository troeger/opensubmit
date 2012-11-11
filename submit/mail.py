from django.core.mail import send_mail
from settings import MAIN_URL

def inform_test_ok(submission):
	subject = 'Your submission was tested successfully'
	message = u'''
		Hi,\n\nthis a short notice that your submission for "%s" in "%s" was tested 
		successfully. No further action is needed.\n\n
		You will get another eMail notification when the grading is finished.\n\n
		Further information can be found at %s.\n\n'''
	message = message%(submission.assignment, submission.assignment.course, MAIN_URL)
	from_email = submission.assignment.course.owner.email
	recipients = submission.authors.values_list('email', flat=True).order_by('email')
	send_mail(subject, message, from_email, recipients, fail_silently=True)

def inform_test_failed(submission):
	subject = 'Warning: Your submission did not pass the test'
	message = u'''Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'''
	message = message%(submission.assignment, submission.assignment.course, MAIN_URL)
	from_email = submission.assignment.course.owner.email
	recipients = submission.authors.values_list('email', flat=True).order_by('email')
	send_mail(subject, message, from_email, recipients, fail_silently=True)

