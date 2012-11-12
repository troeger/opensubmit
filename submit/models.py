from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMessage
from settings import MAIN_URL
import string

valid_fname_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def fname(title):
	title=title.replace(" ","_")
	result=''.join(c for c in title if c in valid_fname_chars)
	return result.lower()

def upload_path(instance, filename):
	course_title=fname(instance.submission.assignment.course.title)
	ass_title=fname(instance.submission.assignment.title)
	subm_title=fname(instance.submission.submitter.get_full_name())
	return '/'.join([course_title, ass_title, subm_title, filename])

class Grading(models.Model):
	title = models.CharField(max_length=20)
	def __unicode__(self):
		return unicode(self.title)

class GradingScheme(models.Model):
	title = models.CharField(max_length=200)
	gradings = models.ManyToManyField(Grading)
	def __unicode__(self):
		return unicode(self.title)

class Course(models.Model):
	title = models.CharField(max_length=200)
	created = models.DateTimeField(auto_now_add=True, editable=False)
	owner   = models.ForeignKey(User, related_name='courses')
	homepage = models.URLField(max_length=200)
	active = models.BooleanField(default=True)
	max_authors = models.PositiveSmallIntegerField(default=1)
	def __unicode__(self):
		return unicode(self.title)

class OpenAssignmentsManager(models.Manager):
	def get_query_set(self):
		return super(OpenAssignmentsManager, self).get_query_set().filter(hard_deadline__gt = timezone.now()).filter(course__active__exact=True)

class Assignment(models.Model):
	title = models.CharField(max_length=200)
	course = models.ForeignKey(Course, related_name='assignments')
	download = models.URLField(max_length=200)
	created = models.DateTimeField(auto_now_add=True, editable=False)
	gradingScheme = models.ForeignKey(GradingScheme)
	published = models.DateTimeField(blank=True, null=True)
	soft_deadline = models.DateTimeField(blank=True, null=True)
	hard_deadline = models.DateTimeField()		# when should the assignment dissappear
	has_attachment = models.BooleanField(default=False)
	test_attachment = models.BooleanField(default=False)
	def __unicode__(self):
		return unicode(self.title)
	objects = models.Manager() # The default manager.
	open_ones = OpenAssignmentsManager() 

class Submission(models.Model):
	RECEIVED = 'R'
	WITHDRAWN = 'W'
	SUBMITTED = 'S'
	SUBMITTED_UNTESTED = 'NT'
	SUBMITTED_COMPILED = 'SC'
	SUBMITTED_TESTED = 'ST'
	FAILED_COMPILE = 'FT'
	FAILED_EXEC = 'FE'
	GRADED_PASS = 'GP'
	GRADED_FAIL = 'GF'
	STATES = (
		(RECEIVED, 'Received'),		# only for initialization, should never shwop up
		(WITHDRAWN, 'Withdrawn'),
		(SUBMITTED, 'Waiting for grading'),
		(SUBMITTED_TESTED, 'Waiting for grading, all tests ok'),
		(SUBMITTED_COMPILED, 'Waiting for execution test'),
		(SUBMITTED_UNTESTED, 'Waiting for compilation test'),
		(FAILED_COMPILE, 'Compilation failed, please re-upload'),
		(FAILED_EXEC, 'Execution failed, please re-upload'),
		(GRADED_PASS, 'Graded - Passed'),
		(GRADED_FAIL, 'Graded - Failed'),
	)

	assignment = models.ForeignKey(Assignment, related_name='submissions')
	submitter = models.ForeignKey(User, related_name='submitted')
	authors = models.ManyToManyField(User, related_name='authored')
	authors.help_text = 'Please add all authors, including yourself.'		
	notes = models.TextField(max_length=200, blank=True)
	created = models.DateTimeField(auto_now_add=True, editable=False)
	grading = models.ForeignKey(Grading, blank=True, null=True)
	grading_notes = models.TextField(max_length=1000, blank=True, null=True)
	state = models.CharField(max_length=2, choices=STATES, default=RECEIVED)
	def __unicode__(self):
		return unicode("Submission %u"%(self.pk))
	def number_of_files(self):
		return self.files.count()
	def authors_list(self):
		return [u.get_full_name() for u in self.authors.all()]
	def can_withdraw(self):
		if self.state == self.WITHDRAWN or self.state == self.SUBMITTED_UNTESTED or self.state == self.SUBMITTED_COMPILED:
			return False
		if self.assignment.hard_deadline < timezone.now():
			# Assignment is over
			return False
		# Hard deadline is not over
		if self.assignment.soft_deadline:
			if self.assignment.soft_deadline < timezone.now():
				# soft deadline is over, allowance of withdrawal here may become configurable later
				return False
			else:
				# Soft deadline is not over 
				# Allow withdrawal only if no tests are pending and no grading occured
				if self.state in [self.SUBMITTED, self.SUBMITTED_TESTED, self.FAILED_COMPILE, self.FAILED_EXEC]:
					return True
				else:
					return False
		else:
			return True
	def can_reupload(self):
		return self.state == self.FAILED_COMPILE or self.state == self.FAILED_EXEC
	def is_withdrawn(self):
		return self.state == self.WITHDRAWN
	def green_tag(self):
		return self.state in [self.GRADED_PASS, self.SUBMITTED_TESTED, self.SUBMITTED]
	def red_tag(self):
		return self.state in [self.GRADED_FAIL, self.FAILED_COMPILE, self.FAILED_EXEC]
	def active_files(self):
		return self.files.filter(replaced_by__isnull=True)

# send mail notification on successful grading
# since this is done in the admin interface, and not in the frontend,
# we trigger it by a save signal
@receiver(post_save, sender=Submission)
def postSubmissionSaveHandler(sender, **kwargs):
	sub=kwargs['instance']
	if sub.state == Submission.GRADED_PASS or sub.state == Submission.GRADED_FAIL:
		inform_student(sub)

class SubmissionFile(models.Model):
	submission = models.ForeignKey(Submission, related_name='files')
	attachment = models.FileField(upload_to=upload_path) 
	fetched = models.DateTimeField(editable=False, null=True)
	output = models.TextField(null=True, blank=True)
	error_code = models.IntegerField(null=True, blank=True)
	replaced_by = models.ForeignKey('SubmissionFile', null=True, blank=True)

# convinienvce function for email information
# to avoid cyclic dependencies, we keep it in the models.py
def inform_student(submission):
	if submission.state == Submission.SUBMITTED_TESTED:
		subject = 'Your submission was tested successfully'
		message = u'Hi,\n\nthis a short notice that your submission for "%s" in "%s" was tested successfully. Compilation and execution worked fine. No further action is needed.\n\nYou will get another eMail notification when the grading is finished.\n\nFurther information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.SUBMITTED_COMPILED:
		subject = 'Your submission was compiled successfully'
		message = u'Hi,\n\nthis a short notice that your submission for "%s" in "%s" was compiled successfully. The execution test is still pending, you will get another eMail notification when it is finished.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.FAILED_COMPILE:
		subject = 'Warning: Your submission did not pass the compilation test'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated compilation test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.FAILED_EXEC:
		subject = 'Warning: Your submission did not pass the execution test'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated execution test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.GRADED_PASS or submission.state == Submission.GRADED_FAIL:
		subject = 'Grading completed'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" was graded.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	else:		
		subject = 'Your submission has a new status'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" has a new status.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)		

	subject = "[%s] %s"%(submission.assignment.course, subject)
	from_email = submission.assignment.course.owner.email
	recipients = submission.authors.values_list('email', flat=True).order_by('email')
	send_mail(subject, message, from_email, recipients, fail_silently=True)
	# send student email with BCC to course owner. This might be configurable later
	email = EmailMessage(subject, message, from_email, recipients, [submission.assignment.course.owner.email])
	email.send(fail_silently=False)

# convinienvce function for email information to the course owner
# to avoid cyclic dependencies, we keep it in the models.py
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

