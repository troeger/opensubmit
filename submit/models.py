from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMessage
from django.core.urlresolvers import reverse
from settings import MAIN_URL, MEDIA_URL
from datetime import date
import string, unicodedata

def upload_path(instance, filename):
	filename=filename.replace(" ","_")
	filename=unicodedata.normalize('NFKD', filename).encode('ascii','ignore').lower()
	return '/'.join([str(date.today().isoformat()),filename])

# monkey patch for getting better user name stringification
# User proxies did not make the job
# Obsolete with Django 1.5 custom User feature
def user_unicode(self):
	return  u'%s %s <%s>' % (self.first_name, self.last_name, self.email)
User.__unicode__ = user_unicode

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
	attachment_test_timeout = models.IntegerField(default=30)
	attachment_test_timeout.help_text = 'Timeout must be smaller than the executor fetch intervall !'
	attachment_test_compile = models.BooleanField(default=False)
	attachment_test_validity = models.FileField(upload_to="testscripts", blank=True, null=True) 
	attachment_test_full = models.FileField(upload_to="testscripts", blank=True, null=True) 
	def attachment_is_tested(self):
		return self.attachment_test_compile == True or self.attachment_test_validity or self.attachment_test_full

	def __unicode__(self):
		return unicode(self.title)
	objects = models.Manager() # The default manager.
	open_ones = OpenAssignmentsManager() 

#class Tutor(models.Model):
#	user = models.ForeignKey(User, related_name='tutor_roles')
#	course = models.ForeignKey(Course, related_name='tutors')		# new course, same tutor -> new record with new students
#	students = 	models.ManyToManyField(User)

class SubmissionFile(models.Model):
	attachment = models.FileField(upload_to=upload_path) 
	fetched = models.DateTimeField(editable=False, null=True)
	test_compile = models.TextField(null=True, blank=True)
	test_validity = models.TextField(null=True, blank=True)
	test_full = models.TextField(null=True, blank=True)
	replaced_by = models.ForeignKey('SubmissionFile', null=True, blank=True)
	def __unicode__(self):
		return unicode(self.attachment.name)
	def basename(self):
		return self.attachment.name[self.attachment.name.rfind('/')+1:]
	def get_absolute_url(self):
		# to implement access protection, we implement our own download
		# this implies that the Apache media serving is disabled
		return reverse('download', args=(self.submissions.all()[0].pk,'attachment'))

class Submission(models.Model):
	RECEIVED = 'R'
	WITHDRAWN = 'W'
	SUBMITTED = 'S'
	TEST_COMPILE_PENDING = 'PC'
	TEST_COMPILE_FAILED = 'FC'
	TEST_VALIDITY_PENDING = 'PV'
	TEST_VALIDITY_FAILED = 'FV'
	TEST_FULL_PENDING = 'PF'
	TEST_FULL_FAILED = 'FF'
	SUBMITTED_TESTED = 'ST'
	GRADED_PASS = 'GP'
	GRADED_FAIL = 'GF'
	STATES = (
		(RECEIVED, 'Received'),		# only for initialization, should never shwop up
		(WITHDRAWN, 'Withdrawn'),
		(SUBMITTED, 'Waiting for grading'),
		(TEST_COMPILE_PENDING, 'Waiting for compilation test'),
		(TEST_COMPILE_FAILED, 'Compilation failed, please re-upload'),
		(TEST_VALIDITY_PENDING, 'Waiting for validation test'),
		(TEST_VALIDITY_FAILED, 'Validation failed, please re-upload'),
		(TEST_FULL_PENDING, 'Waiting for grading (Stage 1)'),
		(TEST_FULL_FAILED, 'Waiting for grading (Stage 2)'),
		(SUBMITTED_TESTED, 'Waiting for grading (Stage 2)'),
		(GRADED_PASS, 'Graded - Passed'),
		(GRADED_FAIL, 'Graded - Failed'),
	)

	assignment = models.ForeignKey(Assignment, related_name='submissions')
	submitter = models.ForeignKey(User, related_name='submitted')
	authors = models.ManyToManyField(User, related_name='authored')
	authors.help_text = ''		
	notes = models.TextField(max_length=200, blank=True)
	file_upload = models.ForeignKey(SubmissionFile, related_name='submissions', blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True, editable=False)
	grading = models.ForeignKey(Grading, blank=True, null=True)
	grading_notes = models.TextField(max_length=1000, blank=True, null=True)
	state = models.CharField(max_length=2, choices=STATES, default=RECEIVED)
	def __unicode__(self):
		return unicode("Submission %u"%(self.pk))
	def can_withdraw(self):
		if self.state in [self.WITHDRAWN, self.TEST_COMPILE_PENDING, self.TEST_VALIDITY_PENDING, self.TEST_FULL_PENDING]: 
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
				if self.state in [self.SUBMITTED, self.SUBMITTED_TESTED, self.TEST_COMPILE_FAILED, self.TEST_VALIDITY_FAILED, self.TEST_FULL_FAILED]:
					return True
				else:
					return False
		else:
			return True
	def can_reupload(self):
		return self.state in [self.TEST_COMPILE_FAILED, self.TEST_VALIDITY_FAILED]
	def is_withdrawn(self):
		return self.state == self.WITHDRAWN
	def green_tag(self):
		return self.state in [self.GRADED_PASS, self.SUBMITTED_TESTED, self.SUBMITTED, self.TEST_FULL_PENDING]
	def red_tag(self):
		return self.state in [self.GRADED_FAIL, self.TEST_COMPILE_FAILED, self.TEST_VALIDITY_FAILED]
	def has_grading(self):
		return self.state in [self.GRADED_FAIL, self.GRADED_PASS]
	def get_initial_state(self):
		if not self.assignment.attachment_is_tested():
			return Submission.SUBMITTED
		else:
			if self.assignment.attachment_test_compile:
				return Submission.TEST_COMPILE_PENDING
			elif self.assignment.attachment_test_validity:
				return Submission.TEST_VALIDITY_PENDING
			elif self.assignment.attachment_test_full:
				return Submission.TEST_FULL_PENDING


# send mail notification on successful grading
# since this is done in the admin interface, and not in the frontend,
# we trigger it by a save signal
@receiver(post_save, sender=Submission)
def postSubmissionSaveHandler(sender, **kwargs):
	sub=kwargs['instance']
	if sub.state == Submission.GRADED_PASS or sub.state == Submission.GRADED_FAIL:
		inform_student(sub)

# convinienvce function for email information
# to avoid cyclic dependencies, we keep it in the models.py
def inform_student(submission):
	if submission.state == Submission.SUBMITTED_TESTED:
		subject = 'Your submission was tested successfully'
		message = u'Hi,\n\nthis a short notice that your submission for "%s" in "%s" was tested successfully. No further action is needed.\n\nYou will get another eMail notification when the grading is finished.\n\nFurther information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.TEST_COMPILE_FAILED:
		subject = 'Warning: Your submission did not pass the compilation test'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated compilation test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.TEST_VALIDITY_FAILED:
		subject = 'Warning: Your submission did not pass the execution test'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated execution test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif submission.state == Submission.GRADED_PASS or submission.state == Submission.GRADED_FAIL:
		subject = 'Grading completed'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" was graded.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	else:
		return

	subject = "[%s] %s"%(submission.assignment.course, subject)
	from_email = submission.assignment.course.owner.email
	recipients = submission.authors.values_list('email', flat=True).distinct().order_by('email')
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

