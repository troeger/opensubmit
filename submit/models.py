from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import string
valid_fname_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def fname(title):
	title=title.replace(" ","_")
	result=''.join(c for c in title if c in valid_fname_chars)
	return result

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
	download = models.URLField(max_length=200, blank=True)
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
	SUBMITTED_TESTED = 'ST'
	UNTESTED = 'NT'
	TEST_FAILED = 'FT'
	GRADED = 'G'
	STATES = (
		(RECEIVED, 'Received'),		# only for initialization, should never shwop up
		(WITHDRAWN, 'Withdrawn'),
		(SUBMITTED, 'Submitted, waiting for grading'),
		(SUBMITTED_TESTED, 'Submitted, tests ok, waiting for grading'),
		(UNTESTED, 'Tests in progress'),
		(TEST_FAILED, 'Tests failed, please re-upload'),
		(GRADED, 'Grading done')
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
		if self.assignment.hard_deadline < timezone.now():
			# Assignment is over
			return False
		# Hard deadline is not over
		if self.assignment.soft_deadline:
			if self.assignment.soft_deadline > timezone.now():
				# soft deadline is over, allowance of withdrawal here may become configurable later
				return False
		# Soft deadline is not over 
		# Allow withdrawal only if no tests are pending and no grading occured
		if self.state == self.SUBMITTED or self.state == self.SUBMITTED_TESTED or self.state == self.TEST_FAILED:
			return True
		else:
			return False
	def is_withdrawn(self):
		return self.state == self.WITHDRAWN

class SubmissionFile(models.Model):
	submission = models.ForeignKey(Submission, related_name='files')
	attachment = models.FileField(upload_to=upload_path) 
	fetched = models.DateTimeField(editable=False, null=True)
	output = models.TextField(null=True, blank=True)
	error_code = models.IntegerField(null=True)
