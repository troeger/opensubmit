import os

import unicodedata

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from opensubmit.models import Assignment, Submission, TestMachine

# Create your models here.


def upload_path(instance, filename):
    '''
        Sanitize the user-provided file name, add timestamp for uniqness.
    '''

    filename = filename.replace(" ", "_")
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').lower()
    return os.path.join(str(timezone.now().date().isoformat()), filename)


class TestMachine(models.Model):
    class Meta:
        permissions = (
            ('api_usage', "The user is allowed to use the API."),
        )

    machine_user = models.OneToOneField(User, primary_key=True)
    name = models.TextField(null=True)
    last_contact = models.DateTimeField(editable=False, blank=True, null=True)

    def __unicode__(self):
        return u'Test machine: {}'.format(self.name)

    def jobs_available(self):
        return TestJob.jobs_available_for(self)

    def jobs_not_completed(self):
        return TestJob.jobs_not_completed_by(self)


class TestJob(models.Model):
    submission = models.OneToOneField(Submission, related_name='job', primary_key=True)
    machine = models.ForeignKey(TestMachine, related_name='jobs', blank=True, null=True)

    @classmethod
    def jobs_available(cls):
        return cls.objects.filter(machine=None)

    @classmethod
    def jobs_available_for(cls, machine):
        if machine is None:
            return cls.jobs_available()
        else:
            return cls.jobs_available().filter(submission__assignment__test__machines=machine, machine=None)

    @classmethod
    def jobs_not_completed_by(cls, machine):
        if machine is None:
            return cls.objects.none()
        else:
            return cls.objects.filter(machine=machine, _result=None)

    def __unicode__(self):
        return u'Test job for: {}'.format(self.submission)

    @property
    def test(self):
        return self.submission.assignment.test

    @property
    def result(self):
        try:
            return self._result
        except TestResult.DoesNotExist:
            return None

    @property
    def assignment_test(self):
        return self.submission.assignment.test


class TestResult(models.Model):
    job = models.OneToOneField(TestJob, related_name='_result', primary_key=True)
    success = models.BooleanField(default=False)

    def __unicode__(self):
        return u'Test result for: {}'.format(self.job.submission)


class TestJobError(models.Model):
    job = models.ForeignKey(TestJob, related_name='errors', editable=False)
    machine = models.ForeignKey(TestMachine, related_name='errors', editable=False)
    occured = models.DateTimeField(auto_now=True, editable=False)
    message = models.TextField(editable=False)


class AssignmentTest(models.Model):
    assignment = models.OneToOneField(Assignment, related_name='test', primary_key=True)
    puppet_config = models.TextField(blank=True)
    machines = models.ManyToManyField(TestMachine, related_name='assignments')
    test_script = models.FileField(upload_to=upload_path, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u'Assignment test for: {}'.format(self.assignment)
