from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMessage
from django.core.urlresolvers import reverse
from settings import MAIN_URL, MEDIA_URL, MEDIA_ROOT
from datetime import date
from itertools import chain
import string, unicodedata

def upload_path(instance, filename):
	filename=filename.replace(" ","_")
	filename=unicodedata.normalize('NFKD', filename).encode('ascii','ignore').lower()
	return '/'.join([str(date.today().isoformat()),filename])

# monkey patch for getting better user name stringification
# User proxies did not make the job
# Obsolete with Django 1.5 custom User feature
def user_unicode(self):
	return  u'%s %s' % (self.first_name, self.last_name)
User.__unicode__ = user_unicode

class Grading(models.Model):
	title = models.CharField(max_length=20)
	means_passed = models.BooleanField(default=True)
	def __unicode__(self):
		return unicode(self.title)

class GradingScheme(models.Model):
	title = models.CharField(max_length=200)
	gradings = models.ManyToManyField(Grading, related_name='schemes')
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

class Assignment(models.Model):
	title = models.CharField(max_length=200)
	course = models.ForeignKey(Course, related_name='assignments')
	download = models.URLField(max_length=200)
	created = models.DateTimeField(auto_now_add=True, editable=False)
	gradingScheme = models.ForeignKey(GradingScheme, related_name="assignments")
	publish_at = models.DateTimeField(default=timezone.now())
	soft_deadline = models.DateTimeField(blank=True, null=True)
	hard_deadline = models.DateTimeField()		# when should the assignment dissappear
	has_attachment = models.BooleanField(default=False)
	attachment_test_timeout = models.IntegerField(default=30)
	attachment_test_compile = models.BooleanField(default=False)
	attachment_test_validity = models.FileField(upload_to="testscripts", blank=True, null=True) 
	validity_script_download = models.BooleanField(default=False)
	attachment_test_full = models.FileField(upload_to="testscripts", blank=True, null=True) 

	def has_validity_test(self):
		return str(self.attachment_test_validity).strip() != ""
	def has_full_test(self):
		return str(self.attachment_test_full).strip() != ""
	def attachment_is_tested(self):
		return self.attachment_test_compile == True or self.has_validity_test() or self.has_full_test()

	def __unicode__(self):
		return unicode(self.title)

#class Tutor(models.Model):
#	user = models.ForeignKey(User, related_name='tutor_roles')
#	course = models.ForeignKey(Course, related_name='tutors')		# new course, same tutor -> new record with new students
#	students = 	models.ManyToManyField(User)

class ValidSubmissionFileManager(models.Manager):
	def get_query_set(self):
		return super(ValidSubmissionFileManager, self).get_query_set().filter(replaced_by=None)

class SubmissionFile(models.Model):
	attachment = models.FileField(upload_to=upload_path) 
	fetched = models.DateTimeField(editable=False, null=True)
	test_compile = models.TextField(null=True, blank=True)
	test_validity = models.TextField(null=True, blank=True)
	test_full = models.TextField(null=True, blank=True)
	perf_data = models.TextField(null=True, blank=True)
	replaced_by = models.ForeignKey('SubmissionFile', null=True, blank=True)
	def __unicode__(self):
		return unicode(self.attachment.name)
	def basename(self):
		return self.attachment.name[self.attachment.name.rfind('/')+1:]
	def get_absolute_url(self):
		# to implement access protection, we implement our own download
		# this implies that the Apache media serving is disabled
		return reverse('download', args=(self.submissions.all()[0].pk,'attachment'))
	def absolute_path(self):
		return MEDIA_ROOT + "/" + self.attachment.name
	def is_executed(self):
		return self.fetched != None
	objects = models.Manager()
	valid_ones = ValidSubmissionFileManager()

class PendingStudentTestsManager(models.Manager):
	def get_query_set(self):
		# compilation wins over validation 
		# the assumption is that the time effort is increasing
		#TODO: Make this one query
		compileJobs = Submission.objects.filter(state=Submission.TEST_COMPILE_PENDING).order_by('-modified')
		validationJobs = Submission.objects.filter(state=Submission.TEST_VALIDITY_PENDING).order_by('-modified')
		return list(chain(compileJobs, validationJobs))

class PendingFullTestsManager(models.Manager):
	def get_query_set(self):
		# Non-graded job validatin wins over closed job re-evaluation
		fullJobs = Submission.objects.filter(state=Submission.TEST_FULL_PENDING).order_by('-modified')
		closedFullJobs = Submission.objects.filter(state=Submission.CLOSED_TEST_FULL_PENDING).order_by('-modified')
		return list(chain(fullJobs, closedFullJobs))

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
	SUBMITTED_TESTED = 'ST'				# All tests ok, waiting for manual grading
	GRADED = 'G'						# Grade and grading notes added, notification pending
	CLOSED = 'C'						# Graded, and students are notified
	CLOSED_TEST_FULL_PENDING = 'CT'		# Keep grading status, but re-run full tests silently
	STATES = (
		(RECEIVED, 'Received'),		# only for initialization, should never shwop up
		(WITHDRAWN, 'Withdrawn'),
		(SUBMITTED, 'Submitted'),
		(TEST_COMPILE_PENDING, 'Compilation test pending'),
		(TEST_COMPILE_FAILED, 'Compilation test failed'),
		(TEST_VALIDITY_PENDING, 'Validity test pending'),
		(TEST_VALIDITY_FAILED, 'Validity test failed'),
		(TEST_FULL_PENDING, 'Full test pending'),
		(TEST_FULL_FAILED, 'Full test failed'),
		(SUBMITTED_TESTED, 'All tests passed'),
		(GRADED, 'Grading in progress'),
		(CLOSED, 'Done'),
		(CLOSED_TEST_FULL_PENDING, 'Done, full test pending')
	)
	STUDENT_STATES = (
		(RECEIVED, 'Received'),		# only for initialization, should never shwop up
		(WITHDRAWN, 'Withdrawn'),
		(SUBMITTED, 'Waiting for grading'),
		(TEST_COMPILE_PENDING, 'Waiting for compilation test'),
		(TEST_COMPILE_FAILED, 'Compilation failed'),
		(TEST_VALIDITY_PENDING, 'Waiting for validation test'),
		(TEST_VALIDITY_FAILED, 'Validation failed'),
		(TEST_FULL_PENDING, 'Waiting for grading'),
		(TEST_FULL_FAILED, 'Waiting for grading'),
		(SUBMITTED_TESTED, 'Waiting for grading'),
		(GRADED, 'Waiting for grading'),
		(CLOSED, 'Graded'),
		(CLOSED_TEST_FULL_PENDING, 'Graded')
	)

	assignment = models.ForeignKey(Assignment, related_name='submissions')
	submitter = models.ForeignKey(User, related_name='submitted')
	authors = models.ManyToManyField(User, related_name='authored')
	authors.help_text = ''		
	notes = models.TextField(max_length=200, blank=True)
	file_upload = models.ForeignKey(SubmissionFile, related_name='submissions', blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True, editable=False)
	modified = models.DateTimeField(auto_now=True, editable=False, blank=True, null=True)
	grading = models.ForeignKey(Grading, blank=True, null=True)
	grading_notes = models.TextField(max_length=1000, blank=True, null=True)
	state = models.CharField(max_length=2, choices=STATES, default=RECEIVED)
	def __unicode__(self):
		return unicode("%u"%(self.pk))
	def can_withdraw(self):
		# No double withdraw
		if self.state == self.WITHDRAWN: 
			return False
		# No withdraw for executed jobs
		# This smells like race condition (page withdraw button rendering -> clicking)
		# Therefore, the withdraw view has to do this check again
		if self.state in [self.TEST_COMPILE_PENDING, self.TEST_VALIDITY_PENDING, self.TEST_FULL_PENDING]: 
			assert(self.file_upload)	# otherwise, the state model is broken
			if self.file_upload.is_executed():
				return False
		# No withdraw for graded jobs
		if self.state == self.GRADED:
			return False			
		# No withdraw for closed jobs
		if self.is_closed():
			return False	
		# In principle, it can be withdrawn
		# Now consider the deadlines
		if self.assignment.hard_deadline < timezone.now():
			# Assignment is over
			return False
		# Hard deadline is not over
		if self.assignment.soft_deadline:
			if self.assignment.soft_deadline < timezone.now():
				# soft deadline is over, allowance of withdrawal here may become configurable later
				return False
		# Soft deadline is not over, or there is no soft deadline 
		return True
	def can_reupload(self):
		# Re-upload should only be possible if the deadlines are not over, which is part of the withdrawal check
		return (self.state in [self.TEST_COMPILE_FAILED, self.TEST_VALIDITY_FAILED]) and self.can_withdraw()
	def is_withdrawn(self):
		return self.state == self.WITHDRAWN
	def is_closed(self):
		return self.state in [self.CLOSED, self.CLOSED_TEST_FULL_PENDING]
	def green_tag(self):
		if self.is_closed() and self.grading:
			return self.grading.means_passed
		else:
			return self.state in [self.SUBMITTED_TESTED, self.SUBMITTED, self.TEST_FULL_PENDING, self.GRADED, self.TEST_FULL_FAILED]
	def red_tag(self):
		if self.is_closed():
			return not self.grading.means_passed
		else:
			return self.state in [self.TEST_COMPILE_FAILED, self.TEST_VALIDITY_FAILED]
	def show_grading(self):	
		return self.is_closed()
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
	def state_for_students(self):
		return dict(self.STUDENT_STATES)[self.state]
	objects = models.Manager()
	pending_student_tests = PendingStudentTestsManager()
	pending_full_tests = PendingFullTestsManager()

class TestMachine(models.Model):
	host = models.TextField(null=True)
	last_contact = 	models.DateTimeField(editable=False)
	config = models.TextField(null=True)

# to avoid cyclic dependencies, we keep it in the models.py
# we hand-in explicitely about which new state we want to inform, since this may not be reflected
# in the model at the moment
def inform_student(submission, state):
	# we cannot send eMail on SUBMITTED_TESTED, since this may have been triggered by test repitition in the backend
	if state == Submission.TEST_COMPILE_FAILED:
		subject = 'Warning: Your submission did not pass the compilation test'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated compilation test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif state == Submission.TEST_VALIDITY_FAILED:
		subject = 'Warning: Your submission did not pass the validation test'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" did not pass the automated validation test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)

	elif state == Submission.CLOSED:
		subject = 'Grading completed'
		message = u'Hi,\n\nthis is a short notice that your submission for "%s" in "%s" was graded.\n\n Further information can be found at %s.\n\n'
		message = message%(submission.assignment, submission.assignment.course, MAIN_URL)
	else:
		return

	subject = "[%s] %s"%(submission.assignment.course, subject)
	from_email = submission.assignment.course.owner.email
	recipients = submission.authors.values_list('email', flat=True).distinct().order_by('email')
	# send student email with BCC to course owner. This might be configurable later
	email = EmailMessage(subject, message, from_email, recipients, [submission.assignment.course.owner.email])
	email.send(fail_silently=True)

# to avoid cyclic dependencies, we keep it in the models.py
def inform_course_owner(request, submission):
	if submission.state == Submission.WITHDRAWN:
		subject = "Submission withdrawn"
		message = "Withdrawn solution %u for '%s'"%(submission.pk, submission.assignment)	

	elif submission.state == Submission.SUBMITTED:
		subject = "Submission ready for grading"
		message = "Solution for '%s' that is ready for grading."%(submission.assignment)	

	elif submission.state == Submission.SUBMITTED_TESTED:
		subject = "Submission tested and ready for grading"
		message = "Solution for '%s' that was tested and is ready for grading."%(submission.assignment)	

	else:
		subject = "Submission changed state"
		message = "Submission has now the state '%s'."%(submission.STATES[submission.state])	

	from_email = submission.assignment.course.owner.email
	recipients = [submission.assignment.course.owner.email]
	send_mail(subject, message, from_email, recipients, fail_silently=True)

