from django.core.mail import send_mail
from settings import MAIN_URL
from models import Submission

def inform_student(submission):
	if submission.state == Submission.SUBMITTED_TESTED:
		subject = 'Your submission was tested successfully'
		message = u'''
			Hi,\n\nthis a short notice that your submission for "%s" in "%s" was tested 
			successfully. Compilation and execution worked fine. No further action is needed.\n\n
			You will get another eMail notification when the grading is finished.\n\n
			Further information can be found at %s.\n\n'''
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.SUBMITTED_COMPILED:
		subject = 'Your submission was compiled successfully'
		message = u'''
			Hi,\n\nthis a short notice that your submission for "%s" in "%s" was compiled 
			successfully. The execution test is still pending, you will get another eMail notification when it is finished.\n\n
			Further information can be found at %s.\n\n'''
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.FAILED_COMPILE:
		subject = 'Warning: Your submission did not pass the compilation test'
		message = u'''Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated compilation test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'''
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.FAILED_EXEC:
		subject = 'Warning: Your submission did not pass the execution test'
		message = u'''Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated execution test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'''
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	else:
		subject = 'Your submission has a new status'
		message = u'''Hi,\n\nthis is a short notice that your submission for "%s" in "%s" has a new status.\n\n Further information can be found at %s.\n\n'''
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	subject = "[%s] %s"%(submission.assignment.course, subject)
	from_email = submission.assignment.course.owner.email
	recipients = submission.authors.values_list('email', flat=True).order_by('email')
	send_mail(subject, message, from_email, recipients, fail_silently=True)
	# send student email with BCC to course owner. This might be configurable later
	email = EmailMessage(subject, message, from_email, recipients, submission.assignment.course.owner.email)
	email.send(fail_silently=False)

def inform_course_owner(request, submission):
	if submission.state == Submission.WITHDRAWN:
		subject = "Submission withdrawn"
		message = "User %s withdrawed solution %u for '%s'"%(request.user, submission.pk, submission.assignment)	

	elif submission.state == Submission.SUBMITTED:
		subject = "Submission ready for grading"
		message = "User %s submitted a solution for '%s' that is ready for grading."%(request.user, submission.assignment)	

	elif submission.state == Submission.SUBMITTED_TESTED:
		subject = "Submission tested and ready for grading"
		message = "User %s submitted a solution for '%s' that was tested and is ready for grading."%(request.user, submission.assignment)	

	else:
		subject = "Submission changed state"
		message = "Submission %u has now the state '%s'."%(submission.pk, submission.STATES[submission.state])	

	from_email = submission.assignment.course.owner.email
	recipients = [submission.assignment.course.owner.email]
	send_mail(subject, message, from_email, recipients, fail_silently=True)
