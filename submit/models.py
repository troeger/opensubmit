from django.db import models
from django.contrib.auth.models import User
import string
valid_fname_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def fname(title):
	result=title.replace(" ","_")
	result=''.join(c for c in title if c in valid_fname_chars)
	return result

def upload_path(instance, filename):
	ass_title=fname(instance.submission.assignment.title)
	subm_title=fname(instance.submission.submitter)
	return '/'.join([ass_title, subm_title, filename])

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
	def __unicode__(self):
		return unicode(self.title)

class StudentGroup(models.Model):
	course = models.ForeignKey(Course, related_name='studentGroups')
	members = models.ManyToManyField(User)

class Assignment(models.Model):
	title = models.CharField(max_length=200)
	course = models.ForeignKey(Course, related_name='assignments')
	created = models.DateTimeField(auto_now_add=True, editable=False)
	gradingScheme = models.ForeignKey(GradingScheme)
	published = models.DateTimeField(blank=True)
	soft_deadline = models.DateTimeField()
	hard_deadline = models.DateTimeField()
	def __unicode__(self):
		return unicode("%s (%s)"%(self.title, self.course))

class SubmissionFile(models.Model):
	file_link = models.FileField(upload_to=upload_path) 

class Submission(models.Model):
	assignment = models.ForeignKey(Assignment, related_name='submissions')
	submitter = models.ForeignKey(User, related_name='submissions')
	notes = models.TextField(max_length=200)
	files = models.ManyToManyField(SubmissionFile, related_name="submission")

class Job(models.Model):
	submission = models.ForeignKey(Submission, related_name='jobs')
	dryrun = models.BooleanField(default=True)
	status = models.CharField(max_length=10)

