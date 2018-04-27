from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

from .submission import Submission
from .submissionfile import SubmissionFile
from .submissiontestresult import SubmissionTestResult

import os
from itertools import groupby

import logging
logger = logging.getLogger('OpenSubmit')


class Assignment(models.Model):
    '''
        An assignment for which students can submit their solution.
    '''

    title = models.CharField(max_length=200)
    course = models.ForeignKey('Course', related_name='assignments')
    download = models.URLField(max_length=200, blank=True, null=True, verbose_name="As link", help_text="External link to the assignment description.")
    description = models.FileField(upload_to="assignment_desc", blank=True, null=True, verbose_name='As file', help_text="Uploaded document with the assignment description.")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    gradingScheme = models.ForeignKey('GradingScheme', related_name="assignments", verbose_name="grading scheme", blank=True, null=True, help_text="Grading scheme for this assignment. Leave empty to have an ungraded assignment.")
    publish_at = models.DateTimeField(default=timezone.now, help_text="Shown for students after this point in time. Users with backend rights always see it.")
    soft_deadline = models.DateTimeField(blank=True, null=True, help_text="Deadline shown to students. After this point in time, submissions are still possible. Leave empty for only using a hard deadline.")
    hard_deadline = models.DateTimeField(blank=True, null=True, help_text="Deadline after which submissions are no longer possible. Can be empty.")
    has_attachment = models.BooleanField(default=False, verbose_name="Student file upload ?", help_text="Activate this if the students must upload a (document / ZIP /TGZ) file as solution. Otherwise, they can only provide notes.")
    attachment_test_timeout = models.IntegerField(default=30, verbose_name="Timout for tests", help_text="Timeout (in seconds) after which the compilation / validation test / full test is cancelled. The submission is marked as invalid in this case. Intended for student code with deadlocks.")
    attachment_test_validity = models.FileField(upload_to="testscripts", blank=True, null=True, verbose_name='Validation script', help_text="If given, the student upload is uncompressed and the script is executed for it on a test machine. Student submissions are marked as valid if this script was successful.")
    validity_script_download = models.BooleanField(default=False, verbose_name='Download of validation script ?', help_text='If activated, the students can download the validation script for offline analysis.')
    attachment_test_full = models.FileField(upload_to="testscripts", blank=True, null=True, verbose_name='Full test script', help_text='Same as the validation script, but executed AFTER the hard deadline to determine final grading criterias for the submission. Results are not shown to students.')
    test_machines = models.ManyToManyField('TestMachine', blank=True, related_name="assignments", help_text="The test machines that will take care of submissions for this assignment.")
    max_authors = models.PositiveSmallIntegerField(default=1, help_text="Maximum number of authors (= group size) for this assignment.")

    class Meta:
        app_label = 'opensubmit'

    def __str__(self):
        return self.title

    def directory_name(self):
        ''' The assignment name in a format that is suitable for a directory name.  '''
        return self.title.replace(" ", "_").replace("\\", "_").replace(",","").lower()

    def directory_name_with_course(self):
        ''' The assignment name in a format that is suitable for a directory name.  '''
        coursename = self.course.directory_name()
        assignmentname = self.title.replace(" ", "_").replace("\\", "_").replace(",","").lower()
        return coursename + os.sep + assignmentname

    def gradable_submissions(self):
        qs = self.valid_submissions()
        qs = qs.filter(state__in=[Submission.GRADING_IN_PROGRESS, Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.SUBMITTED])
        return qs

    def grading_unfinished_submissions(self):
        qs = self.valid_submissions()
        qs = qs.filter(state__in=[Submission.GRADING_IN_PROGRESS])
        return qs

    def graded_submissions(self):
        qs = self.valid_submissions().filter(state__in=[Submission.GRADED])
        return qs

    def grading_url(self):
        '''
            Determines the teacher backend link to the filtered list of gradable submissions for this assignment.
        '''
        grading_url="%s?coursefilter=%u&assignmentfilter=%u&statefilter=tobegraded"%(
                            reverse('teacher:opensubmit_submission_changelist'),
                            self.course.pk, self.pk
                        )
        return grading_url

    def authors(self):
        qs = self.valid_submissions().values_list('authors',flat=True).distinct()
        return qs

    def valid_submissions(self):
        qs = self.submissions.exclude(state=Submission.WITHDRAWN)
        return qs

    def has_perf_results(self):
        '''
            Figure out if any submission for this assignment has performance data being available.
        '''
        num_results = SubmissionTestResult.objects.filter(perf_data__isnull=False).filter(submission_file__submissions__assignment=self).count()
        return num_results != 0

    def is_graded(self):
        '''
        Checks if this a graded assignment.
        '''
        return self.gradingScheme is not None

    def validity_test_url(self):
        '''
            Return absolute download URL for validity test script.
        '''
        if self.pk and self.has_validity_test():
            return settings.HOST + reverse('validity_script_secret', args=[self.pk, settings.JOB_EXECUTOR_SECRET])
        else:
            return None

    def full_test_url(self):
        '''
            Return absolute download URL for full test script.
            Using reverse() seems to be broken with FORCE_SCRIPT in use, so we use direct URL formulation.
        '''
        if self.pk and self.has_full_test():
            return settings.HOST + reverse('full_testscript_secret', args=[self.pk, settings.JOB_EXECUTOR_SECRET])
        else:
            return None

    def url(self):
        '''
            Return absolute URL for assignment description.
        '''
        if self.pk:
            if self.has_description():
                return settings.HOST + reverse('assignment_description_file', args=[self.pk])
            else:
                return self.download
        else:
            return None

    def has_validity_test(self):
        return str(self.attachment_test_validity).strip() != ""

    def has_full_test(self):
        return str(self.attachment_test_full).strip() != ""

    def has_description(self):
        return str(self.description).strip() != ""

    def attachment_is_tested(self):
        return self.has_validity_test() or self.has_full_test()

    def can_create_submission(self, user=None):
        '''
            Central access control for submitting things related to assignments.
        '''
        if user:
            # Super users, course owners and tutors should be able to test their validations
            # before the submission is officially possible.
            # They should also be able to submit after the deadline.
            if user.is_superuser or user is self.course.owner or self.course.tutors.filter(pk=user.pk).exists():
                return True
            if self.course not in user.profile.user_courses():
                # The user is not enrolled in this assignment's course.
                logger.debug('Submission not possible, user not enrolled in the course.')
                return False

            if user.authored.filter(assignment=self).exclude(state=Submission.WITHDRAWN).count() > 0:
                # User already has a valid submission for this assignment.
                logger.debug('Submission not possible, user already has one for this assignment.')
                return False

        if self.hard_deadline and self.hard_deadline < timezone.now():
            # Hard deadline has been reached.
            logger.debug('Submission not possible, hard deadline passed.')
            return False

        if self.publish_at > timezone.now() and not user.profile.can_see_future():
            # The assignment has not yet been published.
            logger.debug('Submission not possible, assignment has not yet been published.')
            return False

        return True

    def add_to_zipfile(self, z):
        if self.description:
            sourcepath = settings.MEDIA_ROOT + self.description.name
            targetpath = self.directory_name_with_course()
            targetname = os.path.basename(self.description.name)
            z.write(sourcepath, targetpath + os.sep + targetname)

    def duplicate_files(self):
        '''
        Search for duplicates of submission file uploads for this assignment.
        This includes the search in other course, whether inactive or not.
        Returns a list of lists, where each latter is a set of duplicate submissions
        with at least on of them for this assignment
        '''
        result=list()
        files = SubmissionFile.valid_ones.order_by('md5')

        for key, dup_group in groupby(files, lambda f: f.md5):
            file_list=[entry for entry in dup_group]
            if len(file_list)>1:
                for entry in file_list:
                    if entry.submissions.filter(assignment=self).count()>0:
                        result.append([key, file_list])
                        break
        return result


